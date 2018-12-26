from py2p import mesh
from py2p import flags
from typing import cast
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import qsort
import numpy as np
import rehash
import time, argparse, asyncio, sys, json, random, os, pickle, base64
import requests

# script argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--matchID", type=str, help="the match filel name to join for this player (node)")
parser.add_argument("-i", "--nodeID", type=int, help="the given node ID")
parser.add_argument("-p", "--port", type=int, help="the opening port number for p2p connection")
parser.add_argument("-b", "--bootstrap", type=int, help="whether this node is a bootstrap node")
parser.add_argument("-a", "--blockchain_addr", type=str, help="the address of the blockchain")
args = parser.parse_args()

# concurrency handler
loop = asyncio.get_event_loop()

# namespace
class initConfig:
    gameID = args.matchID
    port = 0 # my port for opening connection
    bootstrapPort = 0 # port of bootstrap node that accept connection
    sock = "" # socket for connect nodes, send ,recv msg
    ID = "" # my addr ID
    nodeID = args.nodeID

class keyPair:
    priKey = "" # @type str
    pubKey = "" # @type str

class gameConf:
    gamePlyrs = [] # list of player p2p node id with same game match id
    gameOn = False # lock adding players across the global
    matchCompleted = False

class gameRes:
    plyrsSignRes = {} # first key = node id x, second key = known node id from node id x, value = signed game result hash
    plyrsResHash = {}
    plyrsRes = {}
    plyrsPubK = {}

# object
class plyrRes:
    def __init__(self, playerID, win):
        self.playerID = playerID
        self.win = win
    # def __eq__(self, other):
    #     return self.playerID == other.playerID and self.win == other.win

class plyrResList: # = plyrsRes in gameRes
    def __init__(self, plyrResList):
        self.plyrResList = plyrResList
    def getWinner(self):
        for plyrRes in self.plyrResList:
            if plyrRes.win: return plyrRes.playerID

class plyrResList_new:
    def __init__(self, matchData, radiantWins):
        # matchData = [{"gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min", "isRadiant"}, {}, ... ,{}]
        self.matchData = matchData
        self.radiantWins = radiantWins
        self.MVP, self.MVPType = self.getMVP(self.matchData, self.radiantWins)

    def __eq__(self, other):
        return self.matchData == other.matchData and self.radiantWins == other.radiantWins and self.MVP == other.MVP and self.MVPType == other.MVPType

    def getMVP(self, matchData, radiantWins):
        # use highest parameter based total parameter values of all players
        enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]
        plyrRating, ratingBase = {"param": [], "rating": []}, []

        for i in range(0, len(matchData)):
            ratingBase = [matchData[i][j] for j in enum]
        
        for i in range(0, len(matchData)):
            plyrallParam = [(matchData[i][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in range(0, len(enum))]
            plyrRating["param"] += [enum[np.argmax(plyrallParam)]]
            plyrRating["rating"] += [max(plyrallParam)]
        plyrRating["rating"] = np.asarray(plyrRating["rating"])

        plyrWins = np.asarray([matchData[i]["isRadiant"] for i in range(0, len(matchData))])
        return int(np.argmax(plyrRating["rating"][plyrWins])), plyrRating["param"][np.argmax(plyrRating["rating"][plyrWins])]

    def returnMVP(self):
        return gameConf.gamePlyrs[self.MVP]

    def returnDict(self):
        data = {"matchData": self.matchData, "radiantWins": self.radiantWins, "MVP": self.MVP, "MVPType": self.MVPType}
        return data

myConf = initConfig()
myGameConf = gameConf()
# function
def init_keyPair():
    if not os.path.isfile(f"{args.nodeID}.pubKey") or not os.path.isfile(f"{args.nodeID}.pubKey"):
        print("no key pair found, generating new private and public key for node ID.")
        key = RSA.generate(2048)
        keyPair.priKey = key.export_key()
        keyPair.pubKey = key.publickey().export_key()
        with open(f"{args.nodeID}.pubKey", "wb") as pubKeyF:
            pubKeyF.write(key.publickey().export_key())
        with open(f"{args.nodeID}.priKey", "wb") as priKeyF:
            priKeyF.write(key.export_key())
    else:
        print("key pair found, reading existing private and public key for node ID.")
        with open(f"{args.nodeID}.pubKey", "rb") as pubKeyF:
            keyPair.pubKey = pubKeyF.read()
        with open(f"{args.nodeID}.priKey", "rb") as priKeyF:
            keyPair.priKey = priKeyF.read()
    return

def initNode():
    global args, myConf
    # args initializing
    if args.bootstrap is None: args.bootstrap = False
    if args.bootstrap: 
        myConf.port = 1000
    elif args.port == 1000: 
        print("invalid port, please use another port")
        sys.exit()
    else:
        myConf.port = args.port
        myConf.bootstrapPort = 1000

    # p2p network setup
    try:
        myConf.sock = mesh.MeshSocket('0.0.0.0', myConf.port)
    except OSError:
        print("IP and Port pair has already existed")
        sys.exit()
    if not args.bootstrap: myConf.sock.connect('127.0.0.1', myConf.bootstrapPort)
    time.sleep(1)
    myConf.ID = myConf.sock.id
    print("Node "+str(myConf.ID)+" initialized.")
    init_keyPair()

async def readHandler():
    global myGameConf, myConf
    while True:
        if myGameConf.matchCompleted: break

        msg = myConf.sock.recv()
        if msg is not None:
            decodedMsg = msg.packets[1]
            if "handshaking" in decodedMsg and "matchID" in decodedMsg and "pubKey" in decodedMsg:
                if myGameConf.gameOn:
                    print("Request player {} joining existing match".format(str(msg.sender)))
                    msg.reply({"gameOn": 1})
                else:
                    if decodedMsg["matchID"] == myConf.gameID and msg.sender not in myGameConf.gamePlyrs: 
                        pubKey = pickle.loads(decodedMsg["pubKey"])
                        myGameConf.gamePlyrs += [msg.sender]
                        gameRes.plyrsPubK[msg.sender] = pubKey
                    print("Ack new player "+str(msg.sender)+", match ID: "+decodedMsg["matchID"])
                    msg.reply({"ack": 1, "matchID": myConf.gameID, "pubKey": pickle.dumps(keyPair.pubKey)})

            if "ack" in decodedMsg and "matchID" in decodedMsg and "pubKey" in decodedMsg:
                if decodedMsg["matchID"] == myConf.gameID and msg.sender not in myGameConf.gamePlyrs: 
                    pubKey = pickle.loads(decodedMsg["pubKey"])
                    myGameConf.gamePlyrs += [msg.sender]
                    gameRes.plyrsPubK[msg.sender] = pubKey
                print("Received Ack from player "+str(msg.sender)+"match ID: "+decodedMsg["matchID"])

            if "gameOn" in decodedMsg:
                print("Match ID {} has started the match, trying another match session, ID {}".format(myConf.gameID, str(int(myConf.gameID)+1)))
                myConf.gameID = int(myConf.gameID) + 1

            if "pickleSignedGameResHash" in decodedMsg and "exchangeSignedGameResHash" not in decodedMsg:
                signedGameResHash = pickle.loads(decodedMsg["pickleSignedGameResHash"])
                gameResRehash = pickle.loads(decodedMsg["pickleGameResRehash"])

                print("received signed game result hash from player {}".format(str(msg.sender)[0:10]+"..."))
                if myConf.ID not in gameRes.plyrsSignRes: gameRes.plyrsSignRes[myConf.ID] = {}
                if myConf.ID not in gameRes.plyrsResHash: gameRes.plyrsResHash[myConf.ID] = {}
                if msg.sender not in gameRes.plyrsSignRes: gameRes.plyrsSignRes[msg.sender] = {}
                if msg.sender not in gameRes.plyrsResHash: gameRes.plyrsResHash[msg.sender] = {}

                gameRes.plyrsSignRes[myConf.ID][msg.sender] = signedGameResHash
                gameRes.plyrsResHash[myConf.ID][msg.sender] = gameResRehash
                gameRes.plyrsSignRes[msg.sender][msg.sender] = signedGameResHash
                gameRes.plyrsResHash[msg.sender][msg.sender] = gameResRehash

                myConf.sock.send({"pickleGameResRehash": decodedMsg["pickleGameResRehash"], "exchangeSignedGameResHash": 1, "playerID": msg.sender
                , "pickleSignedGameResHash": decodedMsg["pickleSignedGameResHash"]})

            if "exchangeSignedGameResHash" in decodedMsg:
                signedGameResHash = pickle.loads(decodedMsg["pickleSignedGameResHash"])
                gameResRehash = pickle.loads(decodedMsg["pickleGameResRehash"])

                print("received cross-validating signed game result hash of player {} from player {}".format(str(decodedMsg["playerID"])[0:10]+"...", str(msg.sender)[0:10]+"..."))
                if msg.sender not in gameRes.plyrsSignRes: gameRes.plyrsSignRes[msg.sender] = {}
                if msg.sender not in gameRes.plyrsResHash: gameRes.plyrsResHash[msg.sender] = {}
                gameRes.plyrsSignRes[msg.sender][decodedMsg["playerID"]] = signedGameResHash
                gameRes.plyrsResHash[msg.sender][decodedMsg["playerID"]] = gameResRehash

            if "gameRes" in decodedMsg:
                print("received game res from player "+str(msg.sender)[0:10]+"...")
                gameRes.plyrsRes[msg.sender] = decodedMsg["gameRes"]

            if "msg" in decodedMsg:
                print(decodedMsg["msg"])
                

        await asyncio.sleep(1)
    return

def directSend(playerID, msg):
    if playerID not in myConf.sock.routing_table: return playerID
    receiverNode = myConf.sock.routing_table[playerID]
    receiverNode.send(flags.whisper, flags.whisper, msg)
    return

def importGameResult():
    with open(f"{myConf.gameID}", "r") as f:
        content = f.read()
    content = json.loads(content)

    matchData = []
    radiantWins = content["radiant_win"]
    enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]
    for i in range(0, len(content["players"])):
        matchData += [{}]
        for j in enum:
            matchData[i][j] = content["players"][i]["benchmarks"][j]["raw"]
        matchData[i]["isRadiant"] = content["players"][i]["isRadiant"]

    return plyrResList_new(matchData, radiantWins)

def crossVerifyGameRes():
    # check if every signed is valid
    for receiverPID in gameRes.plyrsPubK:
        for senderPID in gameRes.plyrsPubK:
            gameResHash = SHA256.new(gameRes.plyrsRes[receiverPID])
            if gameResHash.hexdigest() != gameRes.plyrsResHash[senderPID][receiverPID].hexdigest():
                return False
            try:
                pkcs1_15.new(RSA.import_key(gameRes.plyrsPubK[receiverPID])).verify(
                    gameResHash, gameRes.plyrsSignRes[senderPID][receiverPID]
                )
            except (ValueError, TypeError):
                return False
    return True

def broadcastOnGameRes(consensusGameRes):
    sortedPubKey = [gameRes.plyrsPubK[i].decode("utf-8") for i in myGameConf.gamePlyrs]
    res =  requests.post(f'http://{args.blockchain_addr}/matches/new'
                , json={'plyrAddrList': sortedPubKey, 'winnerAddr': gameRes.plyrsPubK[consensusGameRes.returnMVP()].decode("utf-8"), 'matchData': consensusGameRes.returnDict()})
    print(res.text)
    return

def consensusOnGameRes():
    # calculate and get the record with most consensus
    matchConsensus = {}
    for basePlayerID, baseResList in gameRes.plyrsRes.items():
        for dump, resList in gameRes.plyrsRes.items():
            if baseResList == resList:
                if basePlayerID not in matchConsensus: matchConsensus[basePlayerID] = 1
                else: matchConsensus[basePlayerID] += 1
    count, consensusPlayerID = max((v, k) for k, v in matchConsensus.items())

    # according to the most consensus record, get the MVP
    consensusGameRes = pickle.loads(gameRes.plyrsRes[consensusPlayerID])
    MVP = consensusGameRes.returnMVP()
    if myConf.ID == MVP:
        print("I am the MVP {}, broadcasting data...".format(MVP))
        broadcastOnGameRes(consensusGameRes)
    else:
        print("I am not the MVP, the MVP is {}".format(MVP))
    return

def broadcastGameHash():
    global myGameConf
    if myConf.ID not in gameRes.plyrsSignRes: gameRes.plyrsSignRes[myConf.ID] = {}
    if myConf.ID not in gameRes.plyrsResHash: gameRes.plyrsResHash[myConf.ID] = {}

    gameRes.plyrsRes[myConf.ID] = pickle.dumps(importGameResult())
    gameResRehash = rehash.sha256(gameRes.plyrsRes[myConf.ID])
    gameResHash = SHA256.new(gameRes.plyrsRes[myConf.ID])
    signedGameResHash = pkcs1_15.new(RSA.import_key(keyPair.priKey)).sign(gameResHash)
    gameRes.plyrsSignRes[myConf.ID][myConf.ID] = signedGameResHash
    gameRes.plyrsResHash[myConf.ID][myConf.ID] = gameResHash

    myConf.sock.send({"pickleGameResRehash": pickle.dumps(gameResRehash)
        , "pickleSignedGameResHash": pickle.dumps(signedGameResHash)})
    return

def broadcastGameRes():
    myConf.sock.send({"gameRes": gameRes.plyrsRes[myConf.ID]})

def sortPlyrs(plyrs):
    # serialize players public key to sort
    plyrsNum = []
    for pid in plyrs:
        plyrsNum += [sum([ord(i) for i in str(gameRes.plyrsPubK[pid])])]
    
    # bubble sort players list for player order consistency among nodes (need stable sort)
    for i in range(0, len(plyrsNum)):
        for j in range(i, len(plyrsNum)):
            if plyrsNum[j] > plyrsNum[i]:
                plyrsNum[j], plyrsNum[i] = plyrsNum[i], plyrsNum[j]
                plyrs[j], plyrs[i] = plyrs[i], plyrs[j]

    return plyrs

async def init_match():
    global myConf, myGameConf
    myGameConf.gamePlyrs += [myConf.ID]
    gameRes.plyrsPubK[myConf.ID] = keyPair.pubKey
    while True:
        if len(myGameConf.gamePlyrs) == 2:
            print("Match {} has 4 players, starting match...".format(myConf.gameID))
            myGameConf.gameOn = True
            time.sleep(2)
            myGameConf.gamePlyrs = sortPlyrs(myGameConf.gamePlyrs)

            # shared turn phase 1: broadcast game hash, signedHash
            # pubKey broadcasted in nodeHandshaking stage
            broadcastGameHash()
            timerOn = time.time()
            curTime = time.time()
            while curTime-timerOn < 60:
                flag = True
                for playerID in gameRes.plyrsSignRes:
                    if len(gameRes.plyrsSignRes[playerID]) != len(myGameConf.gamePlyrs):
                        flag = False
                if flag: break
                await asyncio.sleep(1)
                curTime = time.time()
            if curTime-timerOn >= 60: break

            # shared turn phase 2: broadcast game res, and verify
            broadcastGameRes()
            timerOn = time.time()
            curTime = time.time()
            while curTime-timerOn < 60:
                if len(gameRes.plyrsRes) == len(myGameConf.gamePlyrs): break
                await asyncio.sleep(1)
                curTime = time.time()
            if curTime-timerOn >= 60: break
            matchVerified = crossVerifyGameRes()
            break
        await asyncio.sleep(1)
    
    if curTime-timerOn >= 60:
        print("shared turn time out")
    elif not matchVerified:
        print("match verification failed")
    elif matchVerified:
        print("match verification succeeded, having consensus...")
        consensusOnGameRes()
    myGameConf.matchCompleted = True
    return


def nodeHandshaking():
    global myConf
    if not args.bootstrap:
        handshakingMsg = {"handshaking": 1, "matchID": myConf.gameID, "pubKey": pickle.dumps(keyPair.pubKey)}
        print("Handshaking with mesh network... match ID: "+str(handshakingMsg["matchID"]))
        myConf.sock.send(handshakingMsg)
    try:
        # asyncio.ensure_future(readHandler())
        # loop.run_forever()
        future = [readHandler(), init_match()]
        loop.run_until_complete(asyncio.gather(*future))
    except KeyboardInterrupt:
        pass
    finally:
        print("match completed, ending p2p...")
        loop.close()
    return

initNode()
time.sleep(1)
nodeHandshaking()