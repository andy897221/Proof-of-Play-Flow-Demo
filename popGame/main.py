from py2p import mesh
import sys, json
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request

class plyrData:
    gamePlyrs = []  # list of player p2p node id with same game match id
    plyrsSignRes = {} # first key = node id x, second key = known node id from node id x, value = signed game result hash
    plyrsResHash = {}
    plyrsRes = {}
    plyrsPubK = {}

from sock import *
from config import *
from _helper import *
from cross_verify import *

executor = ThreadPoolExecutor(2)
class main:
    app = Flask(__name__)

    def __init__(self, nodeID, gamePort, keyLoc, APIPort, blockchain_port):
        self.nodeID = nodeID
        self.keyLoc = keyLoc
        self.myConf = config(gamePort, APIPort, self.nodeID)
        self.sk = sock(self.myConf, gameConf, key, plyrData)
        self.cross_verify = cross_verify(plyrData, self.myConf, self.sk, config, blockchain_port)
        self.setup_app()
        return

    ################### conn hosting #########################

    @app.route('/conn', methods=['GET'])
    def establish_connection_with(self):
        content = json.loads(request.data)
        bootstrap = content["bootstrap"] # bootstrap addr string
        matchID = content["matchID"]

        self.sk.sock.connect(bootstrap.split(":")[0], bootstrap.split(":")[1])
        handshakingMsg = {"handshaking": 1, "matchID": matchID, "pubKey": pickle.dumps(key.pubKey)}
        print("Handshaking with mesh network... match ID: " + str(handshakingMsg["matchID"]))
        self.sk.sock.send(handshakingMsg)

        connTimer = 0
        while True:
            if bootstrap in plyrData.gamePlyrs: return json.dumps({'msg': f'connection with {bootstrap} established'}), 200
            connTimer += 1
            if connTimer >= 60: return json.dumps({"msg": "connection failed."}), 408
            time.sleep(1)

    @app.route('/verify', methods=['GET'])
    def verify(self):
        content = json.loads(request.data)
        gameRes = content["gameRec"]

        if len(plyrData.gamePlyrs) != len(gameRes["players"]):
            return json.dumps({'msg', f'number of players of the match doesnt match users of the p2p'}), 400

        executor.submit(cross_verify.start(plyrResList(gameRes)))
        return "match is cross-verifying..."


    ############ conn hosting init #################

    def setup_app(self):
        try:
            self.sk.sock = mesh.MeshSocket('0.0.0.0', self.myConf.port)
        except OSError:
            print("IP and Port pair has already existed")
            sys.exit()

        print("socket established, ready for connection.")
        time.sleep(1)
        self.myConf.ID = self.sk.sock.id

        with open(f"{self.keyLoc}/{self.nodeID}.pubKey", "rb") as pubKeyF:
            key.pubKey = pubKeyF.read()
        with open(f"{self.keyLoc}/{self.nodeID}.priKey", "rb") as priKeyF:
            key.priKey = priKeyF.read()

        print(f"Node {self.myConf.ID} initialized. p2p socket port {self.myConf.port} is running.")
        return

    def run_app(self):
        executor.submit(self.sk.readHandler)
        executor.submit(self.app.run(host='0.0.0.0', port=self.myConf.APIPort))