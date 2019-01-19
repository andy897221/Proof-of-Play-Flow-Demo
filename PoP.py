import PoP_init as _init
import popGame.main as _conn
import popBlockchain.main as _blockchain
import json, os, sys, requests

def path(file):
    return '/'.join(os.path.abspath(file).split("\\")[:-1])

class handler:

    def __init__(self, nodeID, winnerFunc, setupJSON=None):
        from_path = path(sys.argv[0])

        if os.path.isfile(f'{from_path}/config/{nodeID}.json'):
            print(f"{nodeID} config file found.")
        else:
            print(f"{nodeID} config file not found, runnig initialization process...")
            _init.init(nodeID=nodeID, from_path=from_path, setupJSON=setupJSON)

        configFile = f'{from_path}/config/{nodeID}.json'
        if not os.path.isfile(configFile):
            raise FileNotFoundError('conifiguration file not found, please pass setupJSON when creating PoP.handler')
        with open(configFile, "r") as f:
            config = json.loads(f.read())

        self.from_path = from_path
        self.nodeID = nodeID
        self.game_port = config["game_port"]
        self.api_port = config["API_port"]
        self.blockchain_port = config["blockchain_port"]
        self.keyLoc = config["keyLoc"]
        self.blockchainLoc = config["blockchainLoc"]
        self.blockchain_bootstrap_ip = config["blockchain_bootstrap_ip"]
        self.winnerFunc = winnerFunc
        return

    def run_conn(self, matchID):
        def user_func(func):
            def func_wrapper():
                conn = \
                    _conn.main(self.nodeID, self.from_path, matchID, self.winnerFunc, self.game_port, self.keyLoc, self.api_port, self.blockchain_port)
                conn.run_app(func)
            return func_wrapper
        return user_func

    def run_blockchain(self, saveState):
        # bootstrap_addr: the node to connect to retrieve other nodes, None if you are the bootstrap
        # myIP: provide worldwide IP if the blockchain deployment is global, local IP otherwise
        # the above two argument is disabled for simplify features

        # change genesis block, current format matchData {pubKey: {rating, ...}, ...}
        # re generate Bob config file, blockchain_bootstrap_ip should be included
        blockchain = \
            _blockchain.main(self.nodeID, self.blockchain_port, self.blockchain_bootstrap_ip, self.blockchainLoc, self.keyLoc, saveState)
        blockchain.run_app()

    def game_conn_to(self, bootstrap_addr):
        # bootstrap_addr: the node to connect to retrieve other nodes, None if you are the bootstrap
        return requests.post(f"http://127.0.0.1:{self.api_port}/conn",
                      json={'bootstrap': bootstrap_addr}).text

    def verify_game(self, gameRec):
        # how do I receive the result? can I make this a promise?
        res = requests.post(f"http://127.0.0.1:{self.api_port}/verify",
                      json={'gameRec':gameRec})
        if res.status_code == 200:
            res = res.json()
            return res["gameRec"], res["isMVP"]
        else:
            print(res.text)
            return None, None

    def return_plyrList(self):
        return eval(requests.get(f"http://127.0.0.1:{self.api_port}/plyrList").text)

    def terminate(self):
        raise SystemExit