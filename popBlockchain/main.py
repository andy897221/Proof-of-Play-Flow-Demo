import sys
from threading import Thread
from io import BytesIO
from flask import Flask, request, send_file
import logging

class config:
    def __init__(self, nodeID, myPort, bootstrapNode):
        self.knownNodesFile = f"./data/knownNodes{nodeID}.appData"
        self.myPort = myPort
        self.myIP = "127.0.0.1:"+str(self.myPort)
        self.bootstrapNode = bootstrapNode
        return

class consensusSpace:
    timeout = 5
    chainSpace = {} # pubKey is key, {{chain}, endingIndex, startTime, timeout}
    knownLength = {}

from popBlockchain.helper import *
from popBlockchain.blockchain import *
from popBlockchain.key import *

class main:
    def __init__(self, nodeID, myPort, bootstrapNode, fileLoc, keyLoc, saveState, rating_func, auto_broadcast):
        key.pubKey, key.priKey = self.init_key(keyLoc, nodeID)
        self.helper = helper(rating_func, key)
        self.blockchain = Blockchain(fileLoc, nodeID, saveState, self.helper, key, auto_broadcast)
        self.config = config(nodeID, myPort, bootstrapNode)
        return

    @staticmethod
    def init_key(keyLoc, nodeID):
        if not os.path.isfile(f"{keyLoc}/{nodeID}.pubKey") or not os.path.isfile(
                f"{keyLoc}/{nodeID}.priKey"):
            print("no key pair found, non-valid player.")
            sys.exit()
        else:
            with open(f"{keyLoc}/{nodeID}.pubKey", "rb") as pubKeyF:
                pubKey = pubKeyF.read()
            with open(f"{keyLoc}/{nodeID}.priKey", "rb") as priKeyF:
                priKey = priKeyF.read()
        return pubKey, priKey

    @staticmethod
    def create_bytes_msg(myMsg):
        msg = BytesIO()
        msg.write(pickle.dumps(myMsg))
        msg.seek(0)
        return msg

    def start_server(self):
        app = Flask(__name__)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.load_nodes()

        @app.route('/status', methods=['GET'])
        def return_status():
            return json.dumps({'status': 'ok'}), 200

        ################# match hosting #################

        @app.route('/matches/new', methods=['POST'])
        def new_match():
            # add new match
            match = pickle.loads(request.get_data())
            index = self.blockchain.new_match(match)
            response = {'message': f'match will be added to Block {index}'}
            print(response)
            return json.dumps(response), 201

        ################# node hosting ###############

        @app.route('/nodes/register', methods=['POST'])
        def register_nodes():
            nodes = pickle.loads(request.get_data())
            for pubKey in nodes:
                self.blockchain.register_node(nodes, nodes[pubKey])

            # with open(self.config.knownNodesFile, 'w') as knownNode:
            #     knownNode.write(json.dumps(self.blockchain.nodes))

            response = {
                'message': 'New nodes have been added',
                'total_nodes': nodes,
            }
            return json.dumps(response), 201

        @app.route('/nodes/retrieve', methods=['POST'])
        def return_nodes():
            data = request.get_data()
            if data != b'':
                nodes = pickle.loads(request.get_data())
                for nodePubKey, nodeAddr in nodes.items():
                    if nodePubKey not in self.blockchain.nodes: self.blockchain.register_node(nodePubKey, nodeAddr)
            return send_file(self.create_bytes_msg(self.blockchain.nodes),
                             as_attachment=True, attachment_filename="msg")

        ############### chain hosting ##############

        @app.route('/chain', methods=['GET'])
        def full_chain():
            return send_file(self.create_bytes_msg(self.blockchain.chain),
                             as_attachment=True, attachment_filename="msg")

        @app.route('/chain/status', methods=['GET'])
        def chain_status():
            response = {
                'current index': len(self.blockchain.chain),
                'current target': self.blockchain.current_target,
                'current rating': self.blockchain.current_rating,
                'difficulty': self.blockchain.difficulty,
                'pubKey': key.pubKey
            }
            return pickle.dumps(response), 200

        @app.route('/chain/matches', methods=['GET'])
        def current_matches():
            return send_file(self.create_bytes_msg(self.blockchain.current_matches),
                             as_attachment=True, attachment_filename="msg")

        @app.route('/chain/write', methods=['POST'])
        def consensus():
            # dont have checkpoint, pass full chain
            print("request of consensus from others' node recieved.")
            full_chain = pickle.loads(request.get_data())
            res = self.blockchain.resolve_conflict(full_chain)
            if res: response = 'a chain has replaced ours'
            else: response = 'chain has been rejected'
            print(f"response to others: {response}")
            print(f"current target: {self.blockchain.current_target}, current rating: {self.blockchain.current_rating}.")
            return response

        @app.route('/chain/broadcast', methods=['POST'])
        def broadcast():
            self.helper.broadcastResult(self.blockchain.nodes, self.blockchain.chain)
            return "broadcasted", 200

        app.run(host='0.0.0.0', port=self.config.myPort)

    ########### blockchain init #############
    def load_nodes(self):
        self.blockchain.register_node(key.pubKey, self.config.myIP)
        if self.config.bootstrapNode is not None:
            content = pickle.loads(
                requests.post(f'http://{self.config.bootstrapNode}/nodes/retrieve', data=pickle.dumps(self.blockchain.nodes)).content)
            for pubKey, addr in content.items(): self.blockchain.register_node(pubKey, addr)
        self.blockchain.saveState()
        return

    def run_app(self, user_func):
        try:
            server = Thread(target=self.start_server)
            server.daemon = True

            server.start()
            time.sleep(1)
            user_func()
            while True: time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("terminating...")

# Process(target=run_server, args=()).start()