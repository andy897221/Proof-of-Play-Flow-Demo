import sys, time
from multiprocessing import Process
from threading import Thread
sys.path.insert(0, './../')
import PoP
from gameProcess import importGameResult, getRating, getMVP
from mapping import Mapping
import json
import client
import setup
import random

nodeID = None
myPoP = None
blockchainMapping = None
EndChain = False

def get_port():
    configFile = f'config/{nodeID}.json'
    config = json.loads(open(configFile).read())
    return config["external_game_port"], config["game_port"], config["blockchain_port"]

def start(name):
    global nodeID
    global myPoP
    global blockchainMapping
    global EndChain
    terminate()
    nodeID = name
    myPoP = PoP.handler(nodeID=nodeID, winnerFunc=getMVP, ratingFunc=getRating)
    EndChain = False

    @myPoP.run_blockchain(saveState=False, auto_broadcast=True)
    def run_blockchain():
        print("blockchain is running")
        while not EndChain:
            time.sleep(5)
        print("successfully terminate the blockchain")
        myPoP.terminate()
    
    # print("hello")
    # run blockchain
    blockchain = Thread(target=run_blockchain)
    blockchain.daemon = True
    blockchain.start()
    # mapping for the blockchain
    external_game_port, _, blockchain_port = get_port()
    blockchainMapping = Process(target=Mapping(external_game_port + 2, blockchain_port).run)
    blockchainMapping.daemon = True
    blockchainMapping.start()

def terminate():
    if nodeID is None:
        return
    global EndChain
    blockchainMapping.terminate()
    EndChain = True
    # time.sleep(5)

def createClients(thisMatchID, resultFile, dstipsFile):
    dstips = open(dstipsFile, 'r').readlines()

    clientProcesses = []
    for i in range(1):
        ip = dstips[i].replace(' ', ':')
        clientProcess = Process(target=client.run_match, args=(nodeID, i+1, thisMatchID, resultFile, ip, ))
        clientProcess.daemon = True
        clientProcess.start()
        clientProcesses.append(clientProcess)
    
    return clientProcesses

def addBlockchainNodes(dstipsFile):
    dstips = open(dstipsFile, 'r').readlines()
    nodes = dict()
    
    for dst in dstips:
        ip, port = dst.split(' ')
        port = eval(port) + 1
        nodes[str(random.randint())] = ip + ":" + str(port)
    
    myPoP.register_nodes(nodes)

def run_match(thisMatchID, resultFile, dstipsFile):
    @myPoP.run_conn(matchID=thisMatchID)
    def this_match():
        clientProcesses = createClients(thisMatchID, resultFile, dstipsFile)
        addBlockchainNodes(dstipsFile)
        external_game_port, game_port, _ = get_port()
        gameMatch = Process(target=Mapping(external_game_port + 1, game_port).run)
        gameMatch.daemon = True
        gameMatch.start()
        
        while len(myPoP.return_plyrList()) < 2: time.sleep(1)
        plyrList = myPoP.return_plyrList()
        #print(plyrList)
        with open(resultFile, 'r') as f: rawGameResult = f.read()
        gamePlyrList = sorted([item for key, item in plyrList.items()])
        gameResult = importGameResult(rawGameResult, gamePlyrList)

        myPoP.verify_game(gameResult)
        res = myPoP.broadcast_gameRec()
        print(res)

        print(nodeID, "terminated")

        gameMatch.terminate()
        myPoP.terminate()
        for process in clientProcesses:
            process.join()

        return
    this_match()

def get_blockchain():
    print(myPoP.return_chain())

def get_chain_status():
    print(myPoP.return_chain_status())

def get_current_match():
    print(myPoP.return_current_matches())

if __name__ == "__main__":
    name = "Alice"
    setup.setup(name, 7777, 1000, 1001, 1002)
    setup.createGenesis()
    start(name)
    while True:
        command = input(">>> ")
        if (command.split(' ')[0] == "exit"):
            terminate()
            exit(0)
        if (command.split(' ')[0] == "run_match"):
            run_match(command.split(' ')[1], command.split(' ')[2], command.split(' ')[3])
        if (command.split(' ')[0] == "get_blockchain"):
            get_blockchain()
        if (command.split(' ')[0] == "get_chain_status"):
            get_chain_status()
        if (command.split(' ')[0] == "get_current_match"):
            get_current_match()