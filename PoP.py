import PoP_init as _init
import popGame.main as _conn
import popBlockchain.main as _blockchain
import json, os

class handler:

    def __init__(self, nodeID, from_path, setupJSON=None):
        if os.path.isfile(f'{from_path}/config/{nodeID}.json'):
            print(f"{nodeID} config file found.")
        else:
            print(f"{nodeID} config file not found, runnig initialization process...")
            _init.init(nodeID=nodeID, from_path=from_path, setupJSON=setupJSON)

        configFile = f'{from_path}/{nodeID}.json'
        if not os.path.isfile(configFile): raise FileNotFoundError # raise not a valid pop project
        with open(configFile, "r") as f:
            config = json.loads(f.read())
        self.nodeID = nodeID
        self.game_port = config["game_port"]
        self.APIPort = config["API_port"]
        self.blockchain_port = config["blockchain_port"]
        self.keyLoc = config["keyLoc"]
        self.blockchainLoc = config["blockchainLoc"]
        return

    def run_conn(self):
        conn = \
            _conn.main(self.nodeID, self.game_port, self.keyLoc, self.APIPort, self.blockchain_port)
        conn.run_app()

    def game_conn_to(self, bootstrap_addr, matchID):
        # bootstrap_addr: the node to connect to retrieve other nodes, None if you are the bootstrap
        return

    def verify_game(self, gameRec):
        # how do I receive the result? can I make this a promise?
        return

    def run_blockchain(self, saveState, bootstrap_addr, myIP):
        # bootstrap_addr: the node to connect to retrieve other nodes, None if you are the bootstrap
        # myIP: provide worldwide IP if the blockchain deployment is global, local IP otherwise
        blockchain = \
            _blockchain.main(self.nodeID, self.blockchain_port, myIP, bootstrap_addr, self.blockchainLoc, self.keyLoc, saveState)
        blockchain.run_app()