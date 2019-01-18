import sys
sys.path.insert(0, './../') # needed only in example scripts
import PoP
import myGetMVP

# setupJSON needs to be defined if this is the first time the nodeID (user) initialize PoP
nodeID, matchID = "Alice", 1
setupJSON = {
    "nodeID": str(nodeID),
    "game_port": 1000,
    "blockchain_port": 1001,
    "API_port": 1002,
    "blockchain_bootstrap_ip": None,
    # not full parameters are configurated, default paramters will be intialized if it doesn't present in setupJSON
}
PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, setupJSON=setupJSON)

# then config file is then generated