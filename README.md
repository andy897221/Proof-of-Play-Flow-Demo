# Proof-of-Play
Proof-of-Play: A Novel Consensus Model forBlockchain-based Peer-to-Peer Gaming System

## PoP library design
this is an experimental library used as a demo of the idea of Proof-of-Play

## PoP library usage

the PoP object has been be initialized as following:
```python
import PoP
PoP.handler(nodeID="Alice", winnerFunc=None, ratingFunc=None, setupJSON=setupJSON)
```

where setupJSON is the parameter of your PoP blockchain and PoP game
```python
setupJSON = {
    "nodeID": str(nodeID), # the ID of the player, aka an account name
    "game_port": 1000, # the sock port players exchange and verify their game results of the same match
    "blockchain_port": 1001, # the sock port players host their blockchain entry
    "API_port": 1002, # the sock port players trigger the event of game_port
    "blockchain_bootstrap_ip": None, # the ip address of one of the full node blockchain, a bootstrap
    # not full parameters are configurated, default paramters will be intialized if it doesn't present in setupJSON
}
```

the folder ran the above code will then initialized as a PoP project with a config folder, including the public and private key of the player (corresponding to the nodeID), and a .json file storing above setupJSON

##  Example script explanation

### sample_setup_bootstrap.py / sample_setup_client.py

### sample_bootstrap.py / sample_client.py

### sample_bootstrap_blockchain.py / sample_client_blockchain.py

![InternalConsensus](https://github.com/andy897221/Proof-of-Play/blob/master/resources/img/rating.png "P2P")



## Limitation



## Problem

py2p is buggy, there is no safe disconnect for a single node, so for Internal Consensus, no disconnecting features

py2p is not used for blockchain codes