from py2p import mesh
import argparse, sys, json, os
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request

# script argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--matchID", type=str, help="the match filel name to join for this player (node)")
parser.add_argument("-i", "--nodeID", type=int, help="the given node ID")
parser.add_argument("-p", "--port", type=int, help="the opening port number for p2p connection")
parser.add_argument("-q", "--APIPort", type=int, help="the API port")
parser.add_argument("-b", "--bootstrap", type=int, help="whether this node is a bootstrap node")
parser.add_argument("-n", "--playerCount", type=int, help="the number of players in the match (for bootstrap node)")
parser.add_argument("-a", "--blockchain_addr", type=str, help="the address of the blockchain")
parser.add_argument("-k", "--keyLoc", type=str, help="the directory of the pri and pub key")
args = parser.parse_args()

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
    myConf = config(args)

    def __init__(self, args):
        self.myConf = config(args)
        self.sk = sock(self.myConf, gameConf, key, plyrData)
        self.cross_verify = cross_verify(plyrData, self.myConf, self.sk, config, args)
        return

    ################### conn hosting #########################

    app = Flask(__name__)

    @app.route('/conn', methods=['GET'])
    def establish_connection_with():
        content = json.loads(request.data)
        bootstrap = content["bootstrap"]

        if not args.bootstrap:
            handshakingMsg = {"handshaking": 1, "matchID": myConf.gameID, "pubKey": pickle.dumps(key.pubKey)}
            print("Handshaking with mesh network... match ID: " + str(handshakingMsg["matchID"]))
            sk.sock.send(handshakingMsg)
        connTimer = 0
        while True:
            if bootstrap in plyrData.gamePlyrs: return json.dumps({'msg': f'connection with {bootstrap} established'}), 200
            connTimer += 1
            if connTimer >= 60: return json.dumps({"msg": "connection failed."}), 408
            time.sleep(1)

    @app.route('/verify', methods=['GET'])
    def verify():
        content = json.loads(request.data)
        gameRes = content["gameRec"]

        if len(plyrData.gamePlyrs) != len(gameRes["players"]):
            return json.dumps({'msg', f'number of players of the match doesnt match users of the p2p'}), 400

        executor.submit(cross_verify.start(plyrResList(gameRes)))
        return "match is cross-verifying..."


    ############ conn hosting init #################

    def setup_app():
        if args.bootstrap is not None: myConf.bootstrapPort = args.bootstrap
        myConf.port = args.port

        try:
            sk.sock = mesh.MeshSocket('0.0.0.0', myConf.port)
        except OSError:
            print("IP and Port pair has already existed")
            sys.exit()

        if args.bootstrap is None: sk.sock.connect('127.0.0.1', myConf.bootstrapPort)
        time.sleep(1)
        myConf.ID = sk.sock.id

        with open(f"{args.keyLoc}/{args.nodeID}.pubKey", "rb") as pubKeyF:
            key.pubKey = pubKeyF.read()
        with open(f"{args.keyLoc}/{args.nodeID}.priKey", "rb") as priKeyF:
            key.priKey = priKeyF.read()

        print("Node " + str(myConf.ID) + " initialized.")
        return

    def main():
        executor.submit(sk.readHandler)
        setup_app()
        executor.submit(app.run(host='0.0.0.0', port=myConf.APIPort))