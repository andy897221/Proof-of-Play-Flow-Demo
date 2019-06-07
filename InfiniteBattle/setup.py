import sys
sys.path.insert(0, './../') # needed only in example scripts
import PoP
import pickle
import os

def setup(nodeID, external_game_port=7777, game_port=1000, blockchain_port=1001, API_port=1002, SuperNode=None):
    # setupJSON needs to be defined if this is the first time the nodeID (user) initialize PoP
    setupJSON = {
        "nodeID": str(nodeID),
        "external_game_port": external_game_port,
        "game_port": game_port,
        "blockchain_port": blockchain_port,
        "API_port": API_port,
        "blockchain_bootstrap_ip": SuperNode,
        # not full parameters are configurated, default paramters will be intialized if it doesn't present in setupJSON
    }
    PoP.handler(nodeID=nodeID, winnerFunc=None, ratingFunc=None, setupJSON=setupJSON)

    # then config file is then generated

def createGenesis():
    genesis = [{'plyrAddrList': [], 'winnerAddr': None, 'matchData':None}]
    if os.path.exists(f'config/blockchain/genesis_block.data'):
        return
    with open(f'config/blockchain/genesis_block.data', 'wb') as f:
        f.write(pickle.dumps(genesis))