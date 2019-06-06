import sys, time
from multiprocessing import Process
sys.path.insert(0, './../')
import PoP
from gameProcess import importGameResult, getRating, getMVP
from mapping import Mapping
import json
import client
import setup

class PlayerNode:
    def __init__(self):
        self.nodeID = None
    
    def start(self, nodeID):
        self.terminate()
        self.nodeID = nodeID
        self.myPoP = PoP.handler(nodeID=nodeID, winnerFunc=getMVP, ratingFunc=getRating)
        # run blockchain
        self.blockchainProcess = Process(target=self.run_blockchain)
        self.blockchainProcess.daemon = True
        self.blockchainProcess.start()
        configFile = f'config/{nodeID}.json'
        config = json.loads(open(configFile).read())
        self.external_game_port = config["external_game_port"]
        self.game_port = config["game_port"]
        self.blockchain_port = config["blockchain_port"]
        # mapping for the blockchain
        self.blockchainMapping = Process(target=Mapping(self.external_game_port + 2, self.blockchain_port).run)
        self.blockchainMapping.daemon = True
        self.blockchainMapping.start()

    def terminate(self):
        if self.nodeID is None:
            return
        self.blockchainProcess.terminate()
        self.blockchainMapping.terminate()
        self.myPoP.terminate()

    def run_blockchain(self):
        @self.myPoP.run_blockchain(saveState=False, auto_broadcast=True)
        def runningblockchain():
            print("blockchain is running")
            # while True:
            #     time.sleep(5)
            #     print(self.myPoP.return_chain_status())
        runningblockchain()
        

    def run_match(self, thisMatchID, resultFile, dstipsFile):
        dstips = open(dstipsFile, 'r').readlines()
        gameMatch = Process(target=Mapping(self.external_game_port + 1, self.game_port).run)
        gameMatch.daemon = True
        gameMatch.start()
        clientProcesses = []
        for i in range(1):
            ip = dstips[i].replace(' ', ':')
            clientProcess = Process(target=client.run_match, args=(self.nodeID, i+1, thisMatchID, resultFile, ip, ))
            clientProcess.daemon = True
            clientProcess.start()
            clientProcesses.append(clientProcess)
            
        @self.myPoP.run_conn(matchID=thisMatchID)
        def this_match():
            while len(self.myPoP.return_plyrList()) < 2: time.sleep(1)
            plyrList = self.myPoP.return_plyrList()
            with open(resultFile, 'r') as f: rawGameResult = f.read()
            gamePlyrList = sorted([item for key, item in plyrList.items()])
            gameResult = importGameResult(rawGameResult, gamePlyrList)

            self.myPoP.verify_game(gameResult)
            res = self.myPoP.broadcast_gameRec()
            print(res)

            return
        this_match()

        for process in clientProcesses:
            process.join()
        gameMatch.terminate()

if __name__ == "__main__":
    nodeID = "Player"
    setup.setup(nodeID)
    setup.createGenesis()
    player = PlayerNode()
    player.start(nodeID)
    while True:
        command = input(">>> ")
        if (command.split(' ')[0] == "exit"):
            player.terminate()
            exit(0)
        if (command.split(' ')[0] == "run_match"):
            player.run_match(command.split(' ')[1], command.split(' ')[2], command.split(' ')[3])
        