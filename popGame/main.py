from py2p import mesh
import sys, json
from threading import Thread

from flask import Flask, request

class plyrData:
    gamePlyrs = []  # list of player p2p node id with same game match id
    plyrsSignRes = {} # first key = node id x, second key = known node id from node id x, value = signed game result hash
    plyrsResHash = {}
    plyrsRes = {}
    plyrsPubK = {}

from popGame.sock import *
from popGame.config import *
from popGame.helper import *
from popGame.cross_verify import *

class main:

    def __init__(self, nodeID, from_path, matchID, winnerFunc, gamePort, keyLoc, APIPort, blockchain_port):
        self.nodeID = nodeID
        self.from_path = from_path
        self.matchID = matchID
        self.winnerFunc = winnerFunc
        self.keyLoc = keyLoc
        self.myConf = config(gamePort, APIPort, self.nodeID)
        self.gameConf = gameConf(matchID)
        self.sk = sock(self.myConf, self.gameConf, key, plyrData)
        self.cross_verify = cross_verify(plyrData, self.myConf, key, self.gameConf, self.sk, blockchain_port)
        self.setup_app()
        return

    ############ conn hosting init #################

    def setup_app(self):
        try:
            self.sk.sock = mesh.MeshSocket('0.0.0.0', int(self.myConf.port))
        except OSError:
            print("IP and Port pair has already existed")
            sys.exit()

        print("socket established, ready for connection.")
        time.sleep(1)
        self.myConf.ID = self.sk.sock.id

        with open(f"{self.from_path}/{self.keyLoc}/{self.nodeID}.pubKey", "rb") as pubKeyF:
            key.pubKey = pubKeyF.read()
        with open(f"{self.from_path}/{self.keyLoc}/{self.nodeID}.priKey", "rb") as priKeyF:
            key.priKey = priKeyF.read()
        plyrData.plyrsPubK[self.myConf.ID] = key.pubKey

        print(f"Node {self.myConf.ID} initialized. p2p socket port {self.myConf.port} is running.")
        return

    def start_server(self):
        app = Flask(__name__)

        @app.route('/conn', methods=['POST'])
        def establish_connection_with():
            content = json.loads(request.data)
            bootstrap = content["bootstrap"]  # bootstrap addr string

            print(f"Trying to connect to {bootstrap}")
            self.sk.sock.connect(bootstrap.split(":")[0], int(bootstrap.split(":")[1]))
            time.sleep(1)
            handshakingMsg = {"handshaking": 1, "matchID": self.gameConf.matchID, "pubKey": pickle.dumps(key.pubKey)}
            print("Handshaking with mesh network... match ID: " + str(handshakingMsg["matchID"]))
            self.sk.sock.send(handshakingMsg)

            connTimer = 0
            curPlyrLen = len(plyrData.gamePlyrs)
            while True:
                if len(plyrData.gamePlyrs) > curPlyrLen:
                    return f'connection with {bootstrap} established', 200
                connTimer += 1
                if connTimer >= 5: return "connection failed.", 408
                time.sleep(1)

        @app.route('/verify', methods=['GET'])
        def verify():
            content = json.loads(request.data)
            gameRes = content["gameRec"]

            if len(plyrData.gamePlyrs) != len(gameRes["players"]):
                return json.dumps({'msg', f'number of players of the match doesnt match users of the p2p'}), 400

            Thread(target=cross_verify.start, args=(plyrResList(gameRes, self.winnerFunc),)).start()
            return "match is cross-verifying..."

        @app.route('/plyrList', methods=['GET'])
        def return_plyrList():
            return str(plyrData.plyrsPubK), 200

        @app.route('/test', methods=['POST'])
        def test():
            print(request.data)
            return "received data"

        app.run(host='0.0.0.0', port=self.myConf.APIPort)

    def run_app(self, user_func):
        try:
            readHandler = Thread(target=self.sk.readHandler)
            readHandler.daemon = True

            server = Thread(target=self.start_server)
            server.daemon = True

            readHandler.start()
            server.start()
            time.sleep(1)
            user_func()
            while True: time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("terminating...")