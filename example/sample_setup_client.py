import sys
sys.path.insert(0, './../') # needed only in example scripts
import PoP

# setupJSON needs to be defined if this is the first time the nodeID (user) initialize PoP
nodeID = "client"
setupJSON = {
    "nodeID": str(nodeID),
    "game_port": 1003,
    "blockchain_port": 1004,
    "API_port": 1005,
    "blockchain_bootstrap_ip": "127.0.0.1:1001",
    # not full parameters are configurated, default paramters will be intialized if it doesn't present in setupJSON
}
PoP.handler(nodeID=nodeID, winnerFunc=None, ratingFunc=None, setupJSON=setupJSON)

# then config file is then generated