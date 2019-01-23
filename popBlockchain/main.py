import sys
from threading import Thread

from flask import Flask, request, send_file

class config:
    def __init__(self, nodeID, myPort, bootstrapNode):
        self.knownNodesFile = f"./data/knownNodes{nodeID}.appData"
        self.myPort = myPort
        self.myIP = "127.0.0.1"
        self.bootstrapNode = bootstrapNode
        return

from popBlockchain.helper import *
from popBlockchain.blockchain import *
from popBlockchain.key import *

class main:
    def __init__(self, nodeID, myPort, bootstrapNode, fileLoc, keyLoc, saveState, rating_func):
        key.pubKey, key.priKey = self.init_key(keyLoc, nodeID)
        self.blockchain = Blockchain(fileLoc, nodeID, saveState, helper, key, rating_func)
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

    def start_server(self):
        app = Flask(__name__)
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
            nodes = request.get_data()
            for pubKey in nodes:
                self.blockchain.register_node(nodes, nodes[pubKey])

            with open(self.config.knownNodesFile, 'w') as knownNode:
                knownNode.write(json.dumps(self.blockchain.nodes))

            response = {
                'message': 'New nodes have been added',
                'total_nodes': nodes,
            }
            return json.dumps(response), 201

        @app.route('/nodes/retrieve', methods=['GET'])
        def return_nodes():
            return pickle.dumps(self.blockchain.nodes), 200

        ############### chain hosting ##############

        @app.route('/chain', methods=['GET'])
        def full_chain():
            return send_file(pickle.dumps(self.blockchain.chain),
                             as_attachment=True, attachment_filename="msg")

        @app.route('/chain/status', methods=['GET'])
        def chain_status():
            response = {
                'current target': self.blockchain.current_target,
                'current rating': self.blockchain.current_rating,
                'difficulty': self.blockchain.difficulty,
                'pubKey': key.pubKey
            }
            return pickle.dumps(response), 200

        @app.route('/chain/write', methods=['POST'])
        def consensus():
            # dont have checkpoint, pass full chain
            full_chain = pickle.loads(requests.get_data())
            res = self.blockchain.resolve_conflict(full_chain)
            if res: response = {'message': 'a chain has replaced ours'}
            else: response = {'message': 'chain has been rejected'}
            return json.dumps(response), 201

        app.run(host='0.0.0.0', port=self.config.myPort)

    ########### blockchain init #############
    def load_nodes(self):
        self.blockchain.register_node(key.pubKey, self.config.myIP)
        if self.config.bootstrapNode is not None:
            content = pickle.loads(requests.get(f'http://{self.config.bootstrapNode}/nodes/retrieve').content)
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