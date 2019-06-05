# Proof-of-Play: A Novel Consensus Model forBlockchain-based Peer-to-Peer Gaming System
this is an experimental library used as a demo of the idea of Proof-of-Play

## Installation
There is dependence has to be taken care of before using the library:
* Flask
* numpy
* py2p
* pycryptodome
* rehash (url: https://github.com/kislyuk/rehash)

To avoid issues in installation, please use anaconda prompt and create a virtual env (anaconda download link: https://www.anaconda.com/distribution/)

Steps:

after install anaconda, open anaconda prompt and do the following:

```python
conda create -n myPoP python=3.7
```

```python
pip install numpy
```

```python
pip install py2p
```

```python
pip install flask
```

```python
pip install pycryptodome
```

```python
pip install rehash
```

## PoP library usage

### generate users

the PoP object can be initialized as following:
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

### generate genesis

to activate a blockchain one must create a genesis. It defines the data structure of each block. The genesis follows a certain structure due to the implementation of PoP. Note that this step is specific and only if by the following steps can you create the genesis block. It is as follows:

It is a list of dictionary of
```python
genesis = [{'plyrList': [...], 'winnerAddr': pubKey, 'matchData': x}, ...]
```
where:
* plyrList: a dictionary, the list (```[...]```) of players' public key of the match
* winnerAddr: a byte value, the public key (```pubKey```) of the winner
* matchData: any data type for you to manipulate (you need to define ```winnerFunc``` and ```ratingFunc``` later to pick the winner and rate the players respectively in your defined matchData structure

Then, assume you defined the structure above, do:
```python
with open("genesis_block.data", "wb") as f:
    f.write(pickle.dumps(genesis))
```
The genesis_block.data file is created, put the file into the genesis user config folder (this user is responsible to activate this new blockchain). The path is as follows:
* ./config/blockchain/
where the root is the place you ran the setup script for the genesis user.

Note that genesis block can be empty, so you can simply create an empty ```genesis``` with the specific data structure above, and write into the ```genesis_block.data``` file.

##  Example script explanation

script with ```bootstrap``` within the filename means it is setup for a bootstrap node, ```client``` within the filename means it is setup for a client node

## sample_setup_bootstrap.py / sample_setup_client.py

the two script demonstrate the setting up the directory running the script as a PoP project directory

## sample_bootstrap.py / sample_client.py

the two script mainly demonstrate the process shown in the following image:

<img src="https://github.com/andy897221/Proof-of-Play/blob/master/resources/img/verify.png" alt="PoPConn" width="500" height="auto">

both script initialize the PoP object like this:

```python
myPoP = PoP.handler(nodeID=nodeID, winnerFunc=myGetMVP.getMVP, ratingFunc=myGetRating.getRating)
```

where:

winnerFunc (for pop game verification):
* takes game result as function parameter in python standard data structure (i.e. winnerFunc(game_result))
* returns 'winner's public key' in public key data type (bytes, same as .pubKey in config directory) (a single winner)

ratingFunc (for pop blockchain):
* takes game result and a player's public key as function parameter (i.e. ratingFunc(game_result, player_public_key))
* returns a float value as 'rating'

### The sample_bootstrap.py / sample_client.py demonstrate the following process:
1. initialize parameters and PoP object
2. ____main____ wrapper
   1. open a thread and run a function to start the pop blockchain
   2. start a pop match with a provided matchID, terminates after the game result verification completed
   3. set the global variable waitingMatch = False, so that the pop blockchain thread will returns the blockchain status
   4. blockchain thread terminates, the script exits
3. run_match()
   1. use function decorator to start pop match
      1. bootstrap node waits for connection
      2. client node connect to bootstrap node
   2. import arbitrary game result into python standard data structure (1533081738_4035507616_match.data)
   3. verify game result
   4. node broadcast game result (only winner node can successfully broadcast the game result)
4. run_blockchain() (sample_bootstrap.py only)
   1. return chain status after the match has been completed and broadcasted to bootstrap chain (since bootstrap is the winner)


## sample_bootstrap_blockchain.py / sample_client_blockchain.py

the following 2 scripts assumed client script is opened shortly after bootstrap script (about 1 second)

auto_broadcast is set False in the PoP blockchain decorator to show specific blockchain operation example

matches are also generated for demo convenience

### the sample_bootstrap_blockchain.py demonstrate the following process:
1. run_blockchain()
   1. wait for client blockchain (Bob blockchain) connects
   2. generate 5 matches of Alice (this node) wins, this will write 2 blocks
   3. time.sleep(5) to wait for client blockchain operation
   4. broadcast the blockchain to other nodes (i.e. client blockchain)
   5. waiting for client blockchain (client script step 4) to replace this blockchain since client will add two more matches in its blockchain
   6. print the chain status and terminate

#### the sample_client_blockchain.py demonstrate the following process:
1. run_blockchain()
   1. generate 2 matches of Bob (this node) wins, this will write 1 block
   2. waiting for bootstrap node to replace this blockchain, since it is 1 block ahead (bootstrap script step 4)
   3. after bootstrap blockchain has replaced, the 2 matches generated by Bob is not included, yet the 2 matches ratings exceeds the target, so it writes another block immediately (4th block)
   4. broadcast the blockchain to other nodes (i.e. bootstrap blockchain)
   5. print the chain status and terminate

## Not written in the demo

1. both rating function used in the blockchain, and winner function used in the game verification, should be mutually agreed (e.g. blockchain genesis block), but it is not in the blockchain now
2. all of the entry port for both pop game and pop blockchain can be accessed by anyone, no signature verification required
3. validation machine(s) of a match is needed (e.g. start and end time of a match is recorded, cheat detection is implemented etc), or anyone can forge a match and broadcast it

## Problem

py2p disconnect() function doesn't work properly, so there is no safe disconnect feature in pop game
