# Proof-of-Play
Proof-of-Play: A Novel Consensus Model forBlockchain-based Peer-to-Peer Gaming System

## PoPConn.py usage

Internal Consensus of PoP Blockchain

Implementation of the image

![InternalConsensus](img\rating.png)

To run a node, use the following command

Initalize local bootstrap node first, where -b indicates it is bootstrap node, -p indicates the port, -m indicates the match ID

`python PoPConn.py -b 1 -p 1000 -m 1`


then initalize any non bootstrap node, where bootstrap node is assumed as port 1000 in the code

`python PoPConn.py -p 1000 -m 1`

the following image is the demostration of two nodes being connected

![InternalConsensus](/img/exampleRun1.png)

And the following image is the result of a match

![InternalConsensus](/img/exampleRun2.png)