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

# script argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--matchID", type=str, help="the match ID to join for this player (node)")
parser.add_argument("-p", "--port", type=int, help="the opening port number for p2p connection")
parser.add_argument("-b", "--bootstrap", type=int, help="whether this node is a bootstrap node")
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

class keyPair:
    priKey = "" # @type str
    pubKey = "" # @type str

class gameConf:
    gamePlyrs = [] # list of player node id with same game match id
    gameOn = False # lock adding players across the global

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
    def __init__(self, matchData, MVP):
        # matchData = [{gold_pm, xp_pm, kills_pm, lastHit_pm, heroDmg_pm, heroHealing_pm, towerDmg, stuns_pm, isRadiant}, {}, ... ,{}]
        self.matchData = matchData
        self.MVP, self.MVPType = self.getMVP(self.matchData)

    def getMVP(self, matchData):
        # use highest parameter based total parameter values of all players
        enum = ["gold_pm", "xp_pm", "kills_pm", "lastHit_pm", "heroDmg_pm", "heroHealing_pm", "towerDmg", "stuns_pm"]
        plyrRating, ratingBase = {"param": [], "rating": []}, []

        for i in range(0, len(matchData)):
            for j in enum:
                if i == 0: ratingBase.append(matchData[i][j])
                else: ratingBase[j] += matchData[i][j]
        
        for i in range(0, len(matchData)):
            plyrallParam = [(matchData[i][j] / ratingBase) for j in enum]
            plyrRating["param"] += enum[np.argmax(plyrallParam)]
            plyrRating["rating"] += max(plyrallParam)
        return np.argmax(plyrRating["rating"]), plyrRating["param"][np.argmax(plyrRating["Rating"])]

myConf = initConfig()
myGameConf = gameConf()
# function
def genPriKey():

    key = RSA.generate(2048)
    keyPair.priKey = key.export_key()
    keyPair.pubKey = key.publickey().export_key()

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
    genPriKey()

async def readHandler():
    global myGameConf, myConf
    while True:
        msg = myConf.sock.recv()
        if msg is not None:
            decodedMsg = msg.packets[1]
            if "handshaking" in decodedMsg and "matchID" in decodedMsg:
                if myGameConf.gameOn:
                    print("Request player {} joining existing match".format(str(msg.sender)))
                    msg.reply({"gameOn": 1})
                else:
                    if decodedMsg["matchID"] == myConf.gameID and msg.sender not in myGameConf.gamePlyrs: myGameConf.gamePlyrs += [msg.sender]
                    print("Ack new player "+str(msg.sender)+", match ID: "+decodedMsg["matchID"])
                    msg.reply({"ack": 1, "matchID": myConf.gameID})

            if "ack" in decodedMsg and "matchID" in decodedMsg:
                if decodedMsg["matchID"] == myConf.gameID and msg.sender not in myGameConf.gamePlyrs: myGameConf.gamePlyrs += [msg.sender]
                print("Received Ack from player "+str(msg.sender)+"match ID: "+decodedMsg["matchID"])

            if "gameOn" in decodedMsg:
                print("Match ID {} has started the match, trying another match session, ID {}".format(myConf.gameID, str(int(myConf.gameID)+1)))
                myConf.gameID = int(myConf.gameID) + 1

            if "msg" in decodedMsg:
                print(decodedMsg["msg"])

            if "pickleSignedGameResHash" in decodedMsg and "exchangeSignedGameResHash" not in decodedMsg:
                pubKey = pickle.loads(decodedMsg["picklePubKey"])
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
                gameRes.plyrsPubK[msg.sender] = pubKey

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
                

        await asyncio.sleep(1)
    return

def directSend(playerID, msg):
    if playerID not in myConf.sock.routing_table: return playerID
    receiverNode = myConf.sock.routing_table[playerID]
    receiverNode.send(flags.whisper, flags.whisper, msg)
    return

def generateGameResult():
    # player 1 always win, player 1 is the lowest-valued ID defined below
    global myGameConf
    numToPlayerID = {}
    convertedNum = []
    for pid in myGameConf.gamePlyrs:
        convertedNum += [sum([ord(i) for i in str(pid)])]
        numToPlayerID[convertedNum[-1]] = pid
    qsort.qsort(convertedNum)
    winner = numToPlayerID[convertedNum[0]]

    thisResList = plyrResList([plyrRes(playerID, 1) if playerID == winner else plyrRes(playerID, 0) for playerID in myGameConf.gamePlyrs])
    return thisResList

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

def broadcastOnGameRes():

    return

def consensusOnGameRes():
    matchConsensus = {}
    for basePlayerID, baseResList in gameRes.plyrsRes.items():
        for dump, resList in gameRes.plyrsRes.items():
            if baseResList == resList:
                if basePlayerID not in matchConsensus: matchConsensus[basePlayerID] = 1
                else: matchConsensus[basePlayerID] += 1
    count, consensusPlayerID = max((v, k) for k, v in matchConsensus.items())
    winner = pickle.loads(gameRes.plyrsRes[consensusPlayerID]).getWinner()
    if myConf.ID == winner:
        print("I am the winner {}, broadcasting data...".format(winner))
        broadcastOnGameRes()
    else:
        print("I am not the winner, the winner is {}".format(winner))
    return

def broadcastGameHash():
    global myGameConf
    if myConf.ID not in gameRes.plyrsSignRes: gameRes.plyrsSignRes[myConf.ID] = {}
    if myConf.ID not in gameRes.plyrsResHash: gameRes.plyrsResHash[myConf.ID] = {}

    gameRes.plyrsRes[myConf.ID] = pickle.dumps(generateGameResult())
    gameResRehash = rehash.sha256(gameRes.plyrsRes[myConf.ID])
    gameResHash = SHA256.new(gameRes.plyrsRes[myConf.ID])
    signedGameResHash = pkcs1_15.new(RSA.import_key(keyPair.priKey)).sign(gameResHash)
    gameRes.plyrsSignRes[myConf.ID][myConf.ID] = signedGameResHash
    gameRes.plyrsResHash[myConf.ID][myConf.ID] = gameResHash
    gameRes.plyrsPubK[myConf.ID] = keyPair.pubKey

    myConf.sock.send({"pickleGameResRehash": pickle.dumps(gameResRehash)
        , "pickleSignedGameResHash": pickle.dumps(signedGameResHash), "picklePubKey": pickle.dumps(keyPair.pubKey)})
    return

def broadcastGameRes():
    myConf.sock.send({"gameRes": gameRes.plyrsRes[myConf.ID]})

async def init_match():
    global myConf, myGameConf
    myGameConf.gamePlyrs += [myConf.sock.id]
    while True:
        if len(myGameConf.gamePlyrs) == 4:
            print("Match {} has 4 players, starting match...".format(myConf.gameID))
            myGameConf.gameOn = True
            time.sleep(5)

            # shared turn phase 1: broadcast game hash, signedHash and pubKey
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


def nodeHandshaking():
    global myConf
    if not args.bootstrap:
        handshakingMsg = {"handshaking": 1, "matchID": myConf.gameID}
        print("Handshaking with mesh network... "+json.dumps(handshakingMsg))
        myConf.sock.send(handshakingMsg)
    try:
        # asyncio.ensure_future(readHandler())
        # loop.run_forever()
        future = [readHandler(), init_match()]
        loop.run_until_complete(asyncio.gather(*future))
    except KeyboardInterrupt:
        pass
    finally:
        print("ending program...")
        loop.close()
    return

initNode()
time.sleep(1)
nodeHandshaking()