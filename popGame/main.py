from py2p import mesh
import sys, json
from threading import Thread
import requests
from io import BytesIO
from flask import Flask, request, send_file

class plyrData:
    gamePlyrs = []  # list of player p2p node id with same game match id
    plyrsSignRes = {} # first key = node id x, second key = known node id from node id x, value = signed game result hash
    plyrsResHash = {}
    plyrsRes = {}
    plyrsPubK = {}
    consensusGameRes = None

    @staticmethod
    def add_gamePlyrs(plyrSock):
        plyrData.gamePlyrs += [plyrSock]
        plyrData.gamePlyrs = sorted(plyrData.gamePlyrs)

    @staticmethod
    def return_signature():
        signature = {}
        for receiverPID in plyrData.plyrsSignRes:
            signature[plyrData.plyrsPubK[receiverPID]] = {}
            for senderPID in plyrData.plyrsSignRes:
                signature[plyrData.plyrsPubK[receiverPID]][plyrData.plyrsPubK[senderPID]] =\
                    plyrData.plyrsSignRes[receiverPID][senderPID]
        return signature

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
        self.blockchain_port = blockchain_port
        self.cross_verify = cross_verify(plyrData, self.myConf, key, self.gameConf, self.sk)
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
        plyrData.add_gamePlyrs(self.sk.sock.id)

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

        @app.route('/verify', methods=['POST'])
        def verify():
            gameRes = pickle.loads(request.get_data())

            if len(plyrData.plyrsPubK) != len(gameRes):
                return f'number of players ({len(gameRes)}) of the match doesnt match users of the p2p', 400

            # Thread(target=self.cross_verify.start, args=(plyrResList(gameRes, self.winnerFunc),)).start()
            gameRec = plyrResList(matchData=gameRes, winnerFunc=self.winnerFunc,
                                  pubKeyList=[pubKey for sockid, pubKey in plyrData.plyrsPubK.items()])
            gameRec, MVP = self.cross_verify.start(records=gameRec)
            return send_file(self.create_bytes_msg({"gameRec": gameRec, "MVP": MVP}),
                             as_attachment=True, attachment_filename="msg"), 200

        @app.route('/broadcast', methods=['POST'])
        def broadcast():
            if plyrData.consensusGameRes is None:
                return "cross-verify is not completed", 400
            if plyrData.consensusGameRes.returnMVP() != key.pubKey:
                return "you are not the winner, broadcast is not allowed", 400
            data = {'plyrAddrList': plyrData.consensusGameRes.returnPubKeyList(),
                    'winnerAddr': plyrData.consensusGameRes.returnMVP(),
                    'matchData': plyrData.consensusGameRes.returnMatchData(),
                    'signature': plyrData.consensusGameRes.returnSignature()}
            requests.post(f'http://127.0.0.1:{self.blockchain_port}/matches/new', data=pickle.dumps(data))
            return "consensus game result broadcasted", 200

        @app.route('/plyrList', methods=['GET'])
        def return_plyrList():
            return send_file(self.create_bytes_msg(plyrData.plyrsPubK),
                             as_attachment=True, attachment_filename="msg")

        @app.route('/test', methods=['POST'])
        def test():
            print(request.data)
            return "received data", 200

        app.run(host='0.0.0.0', port=self.myConf.APIPort)

    @staticmethod
    def create_bytes_msg(myMsg):
        msg = BytesIO()
        msg.write(pickle.dumps(myMsg))
        msg.seek(0)
        return msg

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