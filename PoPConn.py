from py2p import mesh
from py2p import flags
from typing import cast
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_PSS
import qsort
import numpy as np
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

def getPriKey(priKey): # parse to bytes
    return cast(bytes, priKey)
def getPubKey(pubKey): # parse to bytes
    return cast(bytes, pubKey)

class matchConfig:
    myMatchPlayerIDs = [] # list of player node id with same game match id
    matchStarted = False # lock adding players across the global

class matchResult:
    matchResultFromMyID = {}
    signedResHashFromPlayerID = {} # first key = node id x, second key = known node id from node id x, value = signed game result hash
    gameResFromPlayerID = {}
    pubKFromPlayerID = {}

# object
class playerResult:
    def __init__(self, playerID, win):
        self.playerID = playerID
        self.win = win


nodeConfig = initConfig()
nodeMatchConfig = matchConfig()
# function
def genPriKey():

    key = RSA.generate(2048)
    keyPair.priKey = cast(str, key)
    # file_out = open("private.pem", "wb")
    # file_out.write(private_key)

    keyPair.pubKey = cast(str, key.publickey())
    # public_key = key.publickey().export_key()
    # file_out = open("receiver.pem", "wb")
    # file_out.write(public_key)

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

    genPriKey()

async def readHandler():
    global nodeMatchConfig, nodeConfig
    while True:
        msg = nodeConfig.sock.recv()
        if msg is not None:
            decodedMsg = json.loads(msg.packets[1])

            if "handshaking" in decodedMsg and "matchID" in decodedMsg:
                if nodeMatchConfig.matchStarted:
                    print("Request player {} joining existing match".format(str(msg.sender)))
                    msg.reply(json.dumps({"matchStarted": 1}))
                else:
                    if decodedMsg["matchID"] == nodeConfig.myMatchID: nodeMatchConfig.myMatchPlayerIDs += [msg.sender]
                    print("Ack new player "+str(msg.sender)+", match ID: "+decodedMsg["matchID"])
                    msg.reply(json.dumps({"ack": 1, "matchID": nodeConfig.myMatchID}))

            if "ack" in decodedMsg and "matchID" in decodedMsg:
                if decodedMsg["matchID"] == nodeConfig.myMatchID: nodeMatchConfig.myMatchPlayerIDs += [msg.sender]
                print("Received Ack from player "+str(msg.sender)+"match ID: "+decodedMsg["matchID"])

            if "matchStarted" in decodedMsg:
                print("Match ID {} has started the match, trying another match session, ID {}".format(nodeConfig.myMatchID, nodeConfig.myMatchID+1))
                nodeConfig.myMatchID += 1

            if "signedGameResHash" in decodedMsg and "exchangeSignedGameResHash" not in decodedMsg:
                decodedMsg["signedGameResHash"] = str.encode(decodedMsg["signedGameResHash"])
                decodedMsg["gameRes"] = str.encode(decodedMsg["gameRes"])

                print("received signed game result hash {} from player {}".format(decodedMsg["signedGameResHash"], str(msg.sender)))
                if nodeConfig.myID not in matchResult.signedResHashFromPlayerID: matchResult.signedResHashFromPlayerID[nodeConfig.myID] = {}
                matchResult.signedResHashFromPlayerID[nodeConfig.myID][msg.sender] = decodedMsg["signedGameResHash"]
                matchResult.gameResFromPlayerID[nodeConfig.myID][msg.sender] = decodedMsg["gameRes"]
                matchResult.pubKFromPlayerID[msg.sender] = getPubKey(decodedMsg["pubKey"])
                nodeConfig.sock.send(json.dumps({"gameRes": decodedMsg["gameRes"].decode()
                    , "exchangeSignedGameResHash": 1, "playerID": msg.sender, "signedGameResHash": decodedMsg["signedGameResHash"].decode()}))

            if "exchangeSignedGameResHash" in decodedMsg:
                decodedMsg["signedGameResHash"] = str.encode(decodedMsg["signedGameResHash"])
                decodedMsg["gameRes"] = str.encode(decodedMsg["gameRes"])

                print("received cross-validating signed game result hash {} of player {} from player {}".format(decodedMsg["signedGameResHash"], decodedMsg["playerID"], msg.sender))
                matchResult.signedResHashFromPlayerID[msg.sender][decodedMsg["playerID"]] = decodedMsg["signedGameResHash"]
                matchResult.gameResFromPlayerID[msg.sender][decodedMsg["playerID"]] = decodedMsg["gameRes"]

            if "msg" in decodedMsg:
                print(decodedMsg["msg"])

        await asyncio.sleep(1)
    return

def directSend(playerID, msg):
    if playerID not in nodeConfig.sock.routing_table: return playerID
    receiverNode = nodeConfig.sock.routing_table[playerID]
    receiverNode.send(flags.whisper, flags.whisper, msg)
    return

async def _testDirectSend():
    global nodeMatchConfig 
    while True:
        print(nodeMatchConfig.myMatchPlayerIDs)
        if len(nodeMatchConfig.myMatchPlayerIDs) > 0: 
            notValidList = []
            for playerID in nodeMatchConfig.myMatchPlayerIDs:
                notValid = directSend(playerID, json.dumps({"msg": "hello, whispering from "+str(nodeConfig.myPort)}))
                if notValid is not None: notValidList += [notValid]
            notValidList = np.unique(notValidList)
            for playerID in notValidList: nodeMatchConfig.myMatchPlayerIDs.remove(playerID)
        await asyncio.sleep(1)
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

    gameResult = []
    for playerID in nodeMatchConfig.myMatchPlayerIDs:
        if playerID == winner: gameResult.append(playerResult(playerID, 1))
        else: gameResult.append(playerResult(playerID, 0))
    return gameResult

def crossValidateGameRes():

    # check if every signed is valid
    # check if every game res is same across nodes and correspond to hash
    return

def verifyGameResult():
    # shared turn
    global nodeMatchConfig
    matchResult.matchResultFromMyID[nodeConfig.myID] = pickle.dumps(generateGameResult())
    print(matchResult.matchResultFromMyID[nodeConfig.myID])
    gameResHash = SHA256.new(matchResult.matchResultFromMyID[nodeConfig.myID])
    signedGameResHash = PKCS1_PSS.new(getPriKey(keyPair.priKey)).sign(gameResHash)
    if nodeConfig.myID not in matchResult.signedResHashFromPlayerID: matchResult.signedResHashFromPlayerID[nodeConfig.myID] = {}
    matchResult.signedResHashFromPlayerID[nodeConfig.myID][nodeConfig.myID] = signedGameResHash
    # fix this
    # maybe some pickle msg some json msg? this is pickle
    # nodeConfig.sock.send(json.dumps({"gameRes": matchResult.matchResultFromMyID[nodeConfig.myID]
    #     , "signedGameResHash": signedGameResHash, "pubKey": keyPair.pubKey}))
    print(base64.decodebytes(signedGameResHash))
    nodeConfig.sock.send(json.dumps({"gameRes": matchResult.matchResultFromMyID[nodeConfig.myID]
        , "signedGameResHash": signedGameResHash}))
    return

async def init_match():
    global nodeConfig, nodeMatchConfig
    nodeMatchConfig.myMatchPlayerIDs += [nodeConfig.sock.id]
    while True:
        if len(nodeMatchConfig.myMatchPlayerIDs) >= 4:
            print("Match {} has >= 4 players, starting match...".format(nodeConfig.myMatchID))
            nodeMatchConfig.matchStarted = True
            time.sleep(5)
            verifyGameResult()
            sharedTurnStart = time.time()
            while time.time()-sharedTurnStart < 60:
                print(matchResult.gameResFromPlayerID)
                print(matchResult.signedResHashFromPlayerID)
                # fullGameResExchanged = True
                # for playerID in matchResult.signedResHashFromPlayerID:
                #     if len(matchResult.signedResHashFromPlayerID[playerID]) != len(matchConfig.myMatchPlayerIDs): fullGameResExchanged = False
                # if fullGameResExchanged: crossValidateGameRes()
                await asyncio.sleep(1)
        await asyncio.sleep(1)
    return

def nodeHandshaking():
    global nodeConfig
    if not args.bootstrap:
        handshakingMsg = json.dumps({"handshaking": 1, "matchID": nodeConfig.myMatchID})
        print("Handshaking with mesh network... "+handshakingMsg)
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