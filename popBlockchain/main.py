import sys

from flask import Flask, request

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
    app = Flask(__name__)

    def __init__(self, nodeID, myPort, bootstrapNode, fileLoc, keyLoc, saveState):
        key.pubKey, key.priKey = self.init_key(keyLoc, nodeID)
        self.blockchain = Blockchain(fileLoc, nodeID, saveState, helper, key)
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
            with open(f"{keyLoc}/{nodeID}.pubKey", "rb") as priKeyF:
                priKey = priKeyF.read()
        return pubKey, priKey

    ################ Flask related ###############

    @app.route('/status', methods=['GET'])
    def return_status(self):
        return json.dumps({'status': 'ok'}), 200

    ################# match hosting #################

    @app.route('/matches/new', methods=['POST'])
    def new_match(self):
        # add new match
        match = json.loads(request.data)
        required = ['plyrAddrList', 'winnerAddr', 'matchData']
        if not all(k in match for k in required):
            return 'Missing values', 400
        match['plyrAddrList'] = [bytes(i, encoding='utf-8') for i in match['plyrAddrList']]
        match['winnerAddr'] = bytes(match['winnerAddr'], encoding='utf-8')
        index = self.blockchain.new_match(match)
        response = {'message': f'match will be added to Block {index}'}
        print(response)
        return json.dumps(response), 201

    ################# node hosting ###############

    @app.route('/nodes/register', methods=['POST'])
    def register_nodes(self):
        content = json.loads(request.data)
        nodes = content["nodes"]
        for pubKey in nodes:
            self.blockchain.register_node(pubKey.encode('utf-8'), nodes[pubKey])

        with open(self.config.knownNodesFile, 'w') as knownNode:
            knownNode.write(json.dumps(self.blockchain.nodes))

        response = {
            'message': 'New nodes have been added',
            'total_nodes': nodes,
        }
        return json.dumps(response), 201

    @app.route('/nodes/retrieve', methods=['GET'])
    def return_nodes(self):
        return json.dumps({"nodes": list(self.blockchain.nodes)}), 200

    ############### chain hosting ##############

    @app.route('/chain', methods=['GET'])
    def full_chain(self):
        response = {
            'chain': self.blockchain.chain,
            'length': len(self.blockchain.chain),
        }
        return json.dumps(response), 200

    @app.route('/chain/status', methods=['GET'])
    def chain_status(self):
        response = {
            'current target': self.blockchain.current_target,
            'current rating': self.blockchain.current_rating,
            'difficulty': self.blockchain.difficulty,
            'pubKey': key.pubKey
        }
        return json.dumps(response), 200

    @app.route('/chain/write', methods=['POST'])
    def consensus(self):
        # dont have checkpoint, pass full chain
        full_chain = json.loads(requests.data)["chain"]
        res = self.blockchain.resolve_conflict(full_chain)
        if res: response = {'message': 'a chain has replaced ours'}
        else: response = {'message': 'chain has been rejected'}
        return json.dumps(response), 201

    ########### blockchain init #############
    def load_nodes(self):
        self.blockchain.register_node(key.pubKey, self.config.myIP)
        if os.path.isfile(self.config.knownNodesFile):
            with open(self.config.knownNodesFile, 'r') as content:
                nodes = json.dumps(content)
                for pubKey in nodes: self.blockchain.register_node(pubKey.encode('utf-8'), nodes[pubKey])
            print("nodes has been initialized.")
        else:
            print("no known nodes needed to be added.")

        if self.config.bootstrapNode is not None:
            content = requests.get(f'http://{self.config.bootstrapNode}/nodes/retrieve').text
            requested_nodes = json.loads(content)['nodes']
            for pubKey in requested_nodes: self.blockchain.register_node(pubKey.encode('utf-8'), requested_nodes[pubKey])
            print("new nodes has been added from bootstrap node.")
        self.blockchain.saveState()
        return

    def run_app(self):
        self.load_nodes()
        self.app.run(host='0.0.0.0', port=self.config.myPort)

# Process(target=run_server, args=()).start()