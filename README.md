# Proof-of-Play
Proof-of-Play: A Novel Consensus Model forBlockchain-based Peer-to-Peer Gaming System

## PoPConn.py usage

Internal Consensus of PoP Blockchain

Implementation of the image

![InternalConsensus](https://github.com/andy897221/Proof-of-Play/blob/master/resources/img/rating.png "P2P")

To run a node, use the following command

Initalize local bootstrap node first, where -b indicates it is bootstrap node, -p indicates the port, -m indicates the match data to import (simulate the output of finishing a match) -i indicates the ID/username of the node, for retrieving the public / private key -a indicates the node's blockchain address, to broadcast the match data

`ppython PoPConn.py -b 1 -i 1 -p 1000 -m ./genesis_matches/1533081603_4035506300_match.data -a 127.0.0.1:9000 -k ./nodeKey`


then initalize any non bootstrap node, where bootstrap node is assumed as port 1000 in the code

`python PoPConn.py -i 2 -p 1001 -m ./genesis_matches/1533081603_4035506300_match.data -a 127.0.0.1:9000 -k ./nodeKey`

The following image shows a match of 2 players are initialized and completed, and broadcast to the MVP's blockchain

![InternalConsensus](https://github.com/andy897221/Proof-of-Play/blob/master/resources/img/exampleRun2.PNG "consensus")

## Problem

py2p is buggy, there is no safe disconnect for a single node, so for Internal Consensus, no disconnecting features

py2p is not used for blockchain codes