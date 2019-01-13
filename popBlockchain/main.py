from helper import *
from blockchain import *
from key import *

import json
import os
from multiprocessing import Process
import argparse

import requests
from flask import Flask, request

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bootstrapIP", type=str, help="ip address of bootstrap node")
parser.add_argument("-i", "--nodeID", type=int, help="the id of a node")
parser.add_argument("-k", "--keyLoc", type=str, help="the directory of the pri and pub key")
parser.add_argument("-f", "--fileLoc", type=str, help="blockchain related file location")
parser.add_argument("-s", "--saveState", type=int, help="enable saving blockchain or not (for testing mode)")
parser.add_argument("-p", "--isLocal", type=int, help="ip of local host deployment or public ip deployment")
args = parser.parse_args()
args.saveState = int(args.saveState)
args.isLocal = int(args.isLocal)

#check arg input
if args.fileLoc is None or args.keyLoc is None or args.nodeID is None or args.saveState is None:
    print("please supply all necessary arguments (all except bootstrapIP).")
    exit()

def init_key():
    if not os.path.isfile(f"{args.keyLoc}/{args.nodeID}.pubKey") or not os.path.isfile(f"{args.keyLoc}/{args.nodeID}.priKey"):
        print("no key pair found, non-valid player.")
    else:
        with open(f"{args.keyLoc}/{args.nodeID}.pubKey", "rb") as pubKeyF:
            key.pubKey = pubKeyF.read()
        with open(f"{args.keyLoc}/{args.nodeID}.pubKey", "rb") as priKeyF:
            key.priKey = priKeyF.read()
    return

class config:
    knownNodesFile = f"knownNodes{args.nodeID}.appData"

    myPort = 9000
    if args.bootstrapIP is not None: bootstrapNode = args.bootstrapIP
    else: bootstrapNode = None

    if args.isLocal: myIP = '127.0.0.1'
    else: myIP = requests.get('http://ip.42.pl/raw').text

######### blockchain host ###########

app = Flask(__name__)
blockchain = Blockchain(args, helper)
@app.route('/status', methods=['GET'])
def return_status():
    return json.dumps({'status': 'ok'}), 200

################# match hosting #################

@app.route('/matches/new', methods=['POST'])
def new_match():
    # add new match
    match = json.loads(request.data)
    required = ['plyrAddrList', 'winnerAddr', 'matchData']
    if not all(k in match for k in required):
        return 'Missing values', 400
    match['plyrAddrList'] = [bytes(i, encoding='utf-8') for i in match['plyrAddrList']]
    match['winnerAddr'] = bytes(match['winnerAddr'], encoding='utf-8')
    index = blockchain.new_match(match)
    response = {'message': f'match will be added to Block {index}'}
    print(response)
    return json.dumps(response), 201

################# node hosting ###############

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    content = json.loads(request.data)
    nodes = content["nodes"]
    for pubKey in nodes:
        blockchain.register_node(pubKey.encode('utf-8'), nodes[pubKey])

    with open(config.knownNodesFile, 'w') as knownNode:
        serialize_node = ""
        knownNode.write(json.dumps(blockchain.nodes))

    response = {
        'message': 'New nodes have been added',
        'total_nodes': nodes,
    }
    return json.dumps(response), 201

@app.route('/nodes/retrieve', methods=['GET'])
def return_nodes():
    return json.dumps({"nodes": list(blockchain.nodes)}), 200

############### chain hosting ##############

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return json.dumps(response), 200

@app.route('/chain/status', methods=['GET'])
def chain_status():
    response = {
        'current target': blockchain.current_target,
        'current rating': blockchain.current_rating,
        'difficulty': blockchain.difficulty,
        'pubKey': blockchain.myPubKey
    }
    return json.dumps(response), 200

@app.route('/chain/write', methods=['POST'])
def consensus():
    # dont have checkpoint, pass full chain
    full_chain = json.loads(requests.data)["chain"]
    res = blockchain.resolve_conflict(full_chain)
    if res: response = {'message': 'a chain has replaced ours'}
    else: response = {'message': 'chain has been rejected'}
    return json.dumps(response), 201

########### blockchain init #############
def load_nodes():
    blockchain.register_node(key.pubKey, config.myIP)
    if os.path.isfile(config.knownNodesFile):
        with open(config.knownNodesFile, 'r') as content:
            nodes = json.dumps(content)
            for pubKey in nodes: blockchain.register_node(pubKey.encode('utf-8'), nodes[pubKey])
        print("nodes has been initialized.")
    else:
        print("no known nodes needed to be added.")

    if config.bootstrapNode is not None:
        content = requests.get(f'http://{config.bootstrapNode}/nodes/retrieve').text
        requested_nodes = json.loads(content)['nodes']
        for pubKey in requested_nodes: blockchain.register_node(pubKey.encode('utf-8'), requested_nodes[pubKey])
        print("new nodes has been added from bootstrap node.")
    blockchain.saveState()
    return

def setup_app(app):
    init_key()
    load_nodes()

def main():
    setup_app(app)
    app.run(host='0.0.0.0', port=config.myPort)

# Process(target=run_server, args=()).start()
if __name__ == "__main__":
    main()