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
parser.add_argument("-b", "--bootstrap", type=bool, help="whether this node is a bootstrap node")
parser.add_argument("-c", "--connect", type=int, help=" ")
args = parser.parse_args()

# concurrency handler
loop = asyncio.get_event_loop()

# namespace
class initConfig:
    myMatchID = args.matchID
    myPort = 0 # my port for opening connection
    bootstrapPort = 0 # port of bootstrap node that accept connection
    sock = "" # socket for connect nodes, send ,recv msg
    myID = "" # my addr ID

class keyPair:
    priKey = "" # @type str
    pubKey = "" # @type str

class matchConfig:
    myMatchPlayerIDs = [] # list of player node id with same game match id
    matchStarted = False # lock adding players across the global

class matchResult:
    signedResHashFromPlayerID = {} # first key = node id x, second key = known node id from node id x, value = signed game result hash
    gameResRehashFromPlayerID = {}
    gameResFromPlayerID = {}
    pubKFromPlayerID = {}

# object
class playerResult:
    def __init__(self, playerID, win):
        self.playerID = playerID
        self.win = win
    def __eq__(self, other):
        return self.playerID == other.playerID and self.win == other.win

class playerResultList:
    def __init__(self, playerResultList):
        self.playerResultList = playerResultList
    def __eq__(self, other):
        return self.playerResultList == other.playerResultList
    def getWinner(self):
        for playerResult in self.playerResultList:
            if playerResult.win: return playerResult.playerID

nodeConfig = initConfig()
nodeMatchConfig = matchConfig()
# function
def genPriKey():

    key = RSA.generate(2048)
    keyPair.priKey = key.export_key()
    keyPair.pubKey = key.publickey().export_key()

def initNode():
    global args, nodeConfig
    # args initializing
    if args.bootstrap is None: args.bootstrap = False
    if args.bootstrap: 
        nodeConfig.myPort = 1000
    elif args.port == 1000: 
        print("invalid port, please use another port")
        sys.exit()
    else:
        nodeConfig.myPort = args.port
        nodeConfig.bootstrapPort = 1000

    # p2p network setup
    try:
        nodeConfig.sock = mesh.MeshSocket('0.0.0.0', nodeConfig.myPort)
    except OSError:
        print("IP and Port pair has already existed")
        sys.exit()
    if not args.bootstrap: nodeConfig.sock.connect('127.0.0.1', nodeConfig.bootstrapPort)
    nodeConfig.myID = nodeConfig.sock.id
    print("Node "+str(nodeConfig.myID)+" initialized.")
    genPriKey()

async def readHandler():
    global nodeMatchConfig, nodeConfig
    while True:
        msg = nodeConfig.sock.recv()
        if msg is not None:
            decodedMsg = msg.packets[1]
            if "handshaking" in decodedMsg and "matchID" in decodedMsg:
                if nodeMatchConfig.matchStarted:
                    print("Request player {} joining existing match".format(str(msg.sender)))
                    msg.reply({"matchStarted": 1})
                else:
                    if decodedMsg["matchID"] == nodeConfig.myMatchID and msg.sender not in nodeMatchConfig.myMatchPlayerIDs: nodeMatchConfig.myMatchPlayerIDs += [msg.sender]
                    print("Ack new player "+str(msg.sender)+", match ID: "+decodedMsg["matchID"])
                    msg.reply({"ack": 1, "matchID": nodeConfig.myMatchID})

            if "ack" in decodedMsg and "matchID" in decodedMsg:
                if decodedMsg["matchID"] == nodeConfig.myMatchID and msg.sender not in nodeMatchConfig.myMatchPlayerIDs: nodeMatchConfig.myMatchPlayerIDs += [msg.sender]
                print("Received Ack from player "+str(msg.sender)+"match ID: "+decodedMsg["matchID"])

            if "matchStarted" in decodedMsg:
                print("Match ID {} has started the match, trying another match session, ID {}".format(nodeConfig.myMatchID, str(int(nodeConfig.myMatchID)+1)))
                nodeConfig.myMatchID = int(nodeConfig.myMatchID) + 1

            if "msg" in decodedMsg:
                print(decodedMsg["msg"])

            if "pickleSignedGameResHash" in decodedMsg and "exchangeSignedGameResHash" not in decodedMsg:
                pubKey = pickle.loads(decodedMsg["picklePubKey"])
                signedGameResHash = pickle.loads(decodedMsg["pickleSignedGameResHash"])
                gameResRehash = pickle.loads(decodedMsg["pickleGameResRehash"])

                print("received signed game result hash from player {}".format(str(msg.sender)[0:10]+"..."))
                if nodeConfig.myID not in matchResult.signedResHashFromPlayerID: matchResult.signedResHashFromPlayerID[nodeConfig.myID] = {}
                if nodeConfig.myID not in matchResult.gameResRehashFromPlayerID: matchResult.gameResRehashFromPlayerID[nodeConfig.myID] = {}
                if msg.sender not in matchResult.signedResHashFromPlayerID: matchResult.signedResHashFromPlayerID[msg.sender] = {}
                if msg.sender not in matchResult.gameResRehashFromPlayerID: matchResult.gameResRehashFromPlayerID[msg.sender] = {}

                matchResult.signedResHashFromPlayerID[nodeConfig.myID][msg.sender] = signedGameResHash
                matchResult.gameResRehashFromPlayerID[nodeConfig.myID][msg.sender] = gameResRehash
                matchResult.signedResHashFromPlayerID[msg.sender][msg.sender] = signedGameResHash
                matchResult.gameResRehashFromPlayerID[msg.sender][msg.sender] = gameResRehash
                matchResult.pubKFromPlayerID[msg.sender] = pubKey

                nodeConfig.sock.send({"pickleGameResRehash": decodedMsg["pickleGameResRehash"], "exchangeSignedGameResHash": 1, "playerID": msg.sender
                , "pickleSignedGameResHash": decodedMsg["pickleSignedGameResHash"]})

            if "exchangeSignedGameResHash" in decodedMsg:
                signedGameResHash = pickle.loads(decodedMsg["pickleSignedGameResHash"])
                gameResRehash = pickle.loads(decodedMsg["pickleGameResRehash"])

                print("received cross-validating signed game result hash of player {} from player {}".format(str(decodedMsg["playerID"])[0:10]+"...", str(msg.sender)[0:10]+"..."))
                if msg.sender not in matchResult.signedResHashFromPlayerID: matchResult.signedResHashFromPlayerID[msg.sender] = {}
                if msg.sender not in matchResult.gameResRehashFromPlayerID: matchResult.gameResRehashFromPlayerID[msg.sender] = {}
                matchResult.signedResHashFromPlayerID[msg.sender][decodedMsg["playerID"]] = signedGameResHash
                matchResult.gameResRehashFromPlayerID[msg.sender][decodedMsg["playerID"]] = gameResRehash

            if "gameRes" in decodedMsg:
                print("received game res from player "+str(msg.sender)[0:10]+"...")
                matchResult.gameResFromPlayerID[msg.sender] = decodedMsg["gameRes"]
                

        await asyncio.sleep(1)
    return

def directSend(playerID, msg):
    if playerID not in nodeConfig.sock.routing_table: return playerID
    receiverNode = nodeConfig.sock.routing_table[playerID]
    receiverNode.send(flags.whisper, flags.whisper, msg)
    return

def generateGameResult():
    # player 1 always win, player 1 is the lowest-valued ID defined below
    global nodeMatchConfig
    numToPlayerID = {}
    convertedNum = []
    for pid in nodeMatchConfig.myMatchPlayerIDs:
        convertedNum += [sum([ord(i) for i in str(pid)])]
        numToPlayerID[convertedNum[-1]] = pid
    qsort.qsort(convertedNum)
    winner = numToPlayerID[convertedNum[0]]

    thisResList = playerResultList([playerResult(playerID, 1) if playerID == winner else playerResult(playerID, 0) for playerID in nodeMatchConfig.myMatchPlayerIDs])
    return thisResList

def crossVerifyGameRes():
    # check if every signed is valid
    for receiverPID in matchResult.pubKFromPlayerID:
        for senderPID in matchResult.pubKFromPlayerID:
            gameResHash = SHA256.new(matchResult.gameResFromPlayerID[receiverPID])
            if gameResHash.hexdigest() != matchResult.gameResRehashFromPlayerID[senderPID][receiverPID].hexdigest():
                return False
            try:
                pkcs1_15.new(RSA.import_key(matchResult.pubKFromPlayerID[receiverPID])).verify(
                    gameResHash, matchResult.signedResHashFromPlayerID[senderPID][receiverPID]
                )
            except (ValueError, TypeError):
                return False
    return True

def broadcastOnGameRes():

    return

def consensusOnGameRes():
    matchConsensus = {}
    for basePlayerID, baseResList in matchResult.gameResFromPlayerID.items():
        for playerID, resList in matchResult.gameResFromPlayerID.items():
            if baseResList == resList:
                if basePlayerID not in matchConsensus: matchConsensus[basePlayerID] = 1
                else: matchConsensus[basePlayerID] += 1
    count, consensusPlayerID = max((v, k) for k, v in matchConsensus.items())
    winner = pickle.loads(matchResult.gameResFromPlayerID[consensusPlayerID]).getWinner()
    if nodeConfig.myID == winner:
        print("I am the winner {}, broadcasting data...".format(winner))
        broadcastOnGameRes()
    else:
        print("I am not the winner, the winner is {}".format(winner))
    return

def broadcastGameHash():
    global nodeMatchConfig
    if nodeConfig.myID not in matchResult.signedResHashFromPlayerID: matchResult.signedResHashFromPlayerID[nodeConfig.myID] = {}
    if nodeConfig.myID not in matchResult.gameResRehashFromPlayerID: matchResult.gameResRehashFromPlayerID[nodeConfig.myID] = {}

    matchResult.gameResFromPlayerID[nodeConfig.myID] = pickle.dumps(generateGameResult())
    gameResRehash = rehash.sha256(matchResult.gameResFromPlayerID[nodeConfig.myID])
    gameResHash = SHA256.new(matchResult.gameResFromPlayerID[nodeConfig.myID])
    signedGameResHash = pkcs1_15.new(RSA.import_key(keyPair.priKey)).sign(gameResHash)
    matchResult.signedResHashFromPlayerID[nodeConfig.myID][nodeConfig.myID] = signedGameResHash
    matchResult.gameResRehashFromPlayerID[nodeConfig.myID][nodeConfig.myID] = gameResHash
    matchResult.pubKFromPlayerID[nodeConfig.myID] = keyPair.pubKey

    nodeConfig.sock.send({"pickleGameResRehash": pickle.dumps(gameResRehash)
        , "pickleSignedGameResHash": pickle.dumps(signedGameResHash), "picklePubKey": pickle.dumps(keyPair.pubKey)})
    return

def broadcastGameRes():
    nodeConfig.sock.send({"gameRes": matchResult.gameResFromPlayerID[nodeConfig.myID]})

async def init_match():
    global nodeConfig, nodeMatchConfig
    nodeMatchConfig.myMatchPlayerIDs += [nodeConfig.sock.id]
    while True:
        if len(nodeMatchConfig.myMatchPlayerIDs) >= 4:
            print("Match {} has >= 4 players, starting match...".format(nodeConfig.myMatchID))
            nodeMatchConfig.matchStarted = True
            time.sleep(5)

            # shared turn phase 1: broadcast game hash, signedHash and pubKey
            broadcastGameHash()
            sharedTurnStart = time.time()
            curTime = time.time()
            while curTime-sharedTurnStart < 60:
                fullGameResHashExchanged = True
                for playerID in matchResult.signedResHashFromPlayerID:
                    if len(matchResult.signedResHashFromPlayerID[playerID]) != len(matchConfig.myMatchPlayerIDs):
                        fullGameResHashExchanged = False
                if fullGameResHashExchanged: break
                await asyncio.sleep(1)
                curTime = time.time()
            if curTime-sharedTurnStart >= 60: break

            # shared turn phase 2: broadcast game res, and verify
            broadcastGameRes()
            sharedTurnStart = time.time()
            curTime = time.time()
            while curTime-sharedTurnStart < 60:
                if len(matchResult.gameResFromPlayerID) == len(matchConfig.myMatchPlayerIDs): break
                await asyncio.sleep(1)
                curTime = time.time()
            if curTime-sharedTurnStart >= 60: break
            matchVerified = crossVerifyGameRes()
            break
        await asyncio.sleep(1)
    
    if curTime-sharedTurnStart >= 60:
        print("shared turn time out")
    elif not matchVerified:
        print("match verification failed")
    elif matchVerified:
        print("match verification succeeded, having consensus...")
        consensusOnGameRes()


def nodeHandshaking():
    global nodeConfig
    if not args.bootstrap:
        handshakingMsg = {"handshaking": 1, "matchID": nodeConfig.myMatchID}
        print("Handshaking with mesh network... "+json.dumps(handshakingMsg))
        nodeConfig.sock.send(handshakingMsg)
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