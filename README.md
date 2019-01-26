# Proof-of-Play: A Novel Consensus Model forBlockchain-based Peer-to-Peer Gaming System
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

the folder ran the above code will then initialized as a PoP project with a config folder, with a .json file storing above setupJSON

##  Example script explanation

script with ```bootstrap``` within the filename means it is setup for a bootstrap node, ```client``` within the filename means it is setup for a client node

### sample_setup_bootstrap.py / sample_setup_client.py

the two script demonstrate the setting up the directory running the script as a PoP project directory

### sample_bootstrap.py / sample_client.py

the two script mainly demonstrate the process shown in the following image:

<img src="(https://github.com/andy897221/Proof-of-Play/blob/master/resources/img/verify.png" alt="PoPConn" width="100" height="auto">

both script initialize the PoP object like this:

```python
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, ratingFunc=myGetRating.getRating)
```

where,\
winnerFunc (for pop game verification): takes game result as function parameter in python standard data structure (i.e. winnerFunc(game_result)) and returns 'winner's public key' (a single winner),\
ratingFunc (for pop blockchain): takes game result and a player's public key as function parameter (i.e. ratingFunc(game_result, player_public_key)) and returns a float value as 'rating'

The sample_bootstrap.py demonstrate the following process:



### sample_bootstrap_blockchain.py / sample_client_blockchain.py



## Limitation



## Problem

py2p is buggy, there is no safe disconnect for a single node, so for Internal Consensus, no disconnecting features

py2p is not used for blockchain codes