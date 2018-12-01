# Proof-of-Play
Proof-of-Play: A Novel Consensus Model forBlockchain-based Peer-to-Peer Gaming System

## PoPConn.py usage

Internal Consensus of PoP Blockchain

Implementation of the image

![InternalConsensus](https://github.com/andy897221/Proof-of-Play/blob/master/img/rating.png "P2P")

To run a node, use the following command

Initalize local bootstrap node first, where -b indicates it is bootstrap node, -p indicates the port, -m indicates the match ID

`python PoPConn.py -b 1 -p 1000 -m 1`


then initalize any non bootstrap node, where bootstrap node is assumed as port 1000 in the code

`python PoPConn.py -p 1000 -m 1`

the following image is the demostration of two nodes being connected

![InternalConsensus](https://github.com/andy897221/Proof-of-Play/blob/master/img/exampleRun1.PNG "init")

And the following image is the result of a match

![InternalConsensus](https://github.com/andy897221/Proof-of-Play/blob/master/img/exampleRun2.PNG "consensus")

## Problem

py2p is buggy, there is no safe disconnect for a single node, so for Internal Consensus, no disconnecting features

py2p is not used for blockchain codes