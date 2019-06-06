import sys, time
sys.path.insert(0, './../')
import PoP
from gameProcess import importGameResult, getRating, getMVP
import json
import shutil, os

def run_match(nodeID, clientID, thisMatchID, resultFile, dstip):
    # initial file
    configFile = f'config/{nodeID}.json'
    config = json.loads(open(configFile).read())
    setup_frame = {}
    setup_frame["nodeID"] = nodeID + "_Client_" + str(clientID)
    setup_frame["game_port"] = config["game_port"] + 3 * clientID
    setup_frame["blockchain_port"] = config["blockchain_port"] + 3 * clientID
    setup_frame["API_port"] = config["API_port"] + 3 * clientID
    setup_frame["blockchain_bootstrap_ip"] = "127.0.0.1:" + str(config["blockchain_port"])
    setup_frame["keyLoc"] = "./config/nodeKey"
    setup_frame["blockchainLoc"] = "./config/blockchain"
    shutil.copyfile(f'config/nodeKey/{nodeID}.priKey', f'config/nodeKey/{setup_frame["nodeID"]}.priKey')
    shutil.copyfile(f'config/nodeKey/{nodeID}.pubKey', f'config/nodeKey/{setup_frame["nodeID"]}.pubKey')
    shutil.copyfile(f'config/blockchain/{nodeID}.blockchain', f'config/blockchain/{setup_frame["nodeID"]}.blockchain')
    with open(f"./config/{setup_frame['nodeID']}.json", "w") as f:
        f.write(json.dumps(setup_frame))
    myPoP = PoP.handler(nodeID=setup_frame["nodeID"], winnerFunc=getMVP, ratingFunc=getRating)
    
    @myPoP.run_conn(matchID=thisMatchID)
    def my_match():
        ########## API entry and p2p entry threads are running, you can execute any code here ##########

        # create a two player pop match
        time.sleep(10)
        myPoP.game_conn_to(dstip) # connect to bootstrap node

        plyrList = myPoP.return_plyrList()
        
        with open(resultFile, 'r') as f: rawGameRec = f.read()
        gamePlyrList = sorted([item for key, item in plyrList.items()]) # assume the match records corresponds to this plyr list
        gameRec = importGameResult(rawGameRec, gamePlyrList)

        myPoP.verify_game(gameRec)
        # res = myPoP.broadcast_gameRec()
        # print(res)
        time.sleep(10)

        myPoP.terminate() # pop will only be terminated if this is ran, otherwise it freeze at the end of this function
        return
    my_match()

    os.remove(f'config/nodeKey/{setup_frame["nodeID"]}.priKey')
    os.remove(f'config/nodeKey/{setup_frame["nodeID"]}.pubKey')
    os.remove(f'config/blockchain/{setup_frame["nodeID"]}.blockchain')
    os.remove(f"./config/{setup_frame['nodeID']}.json")
    