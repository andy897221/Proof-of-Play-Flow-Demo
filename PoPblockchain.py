import hashlib
import json
from time import time
import time
import os
from urllib.parse import urlparse
from uuid import uuid4
from multiprocessing import Process
import argparse

import requests
from flask import Flask, jsonify, request

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bootstrapIP", type=str, help="ip address of bootstrap node")
parser.add_argument("-i", "--nodeID", type=int, help="the id of a node")
parser.add_argument("-k", "--keyLoc", type=str, help="the directory of the pri and pub key")
parser.add_argument("-f", "--fileLoc", type=str, help="blockchain file location")
parser.add_argument("-s", "--saveState", type=int, help="enable saving blockchain or not (for testing mode)")
args = parser.parse_args()

class helper:
    def get_rating(matchData, plyrIndex):
        enum = ["gold_per_min", "xp_per_min", "kills_per_min", "last_hits_per_min", "hero_damage_per_min", "hero_healing_per_min", "tower_damage", "stuns_per_min"]
        plyrRating, ratingBase = {"param": 0, "rating": 0}, []
        for i in range(0, len(matchData)):
            ratingBase += [[matchData[i][j] for j in enum]]
        ratingBase = list(np.asarray(ratingBase).sum(axis=0))

        plyrallParam = [(matchData[plyrIndex][enum[j]] / ratingBase[j]) if ratingBase[j] != 0 else 0 for j in range(0, len(enum))]
        plyrRating["param"] = [enum[np.argmax(plyrallParam)]]
        plyrRating["rating"] = [max(plyrallParam)]
        return plyrRating["rating"], plyrRating["param"]

    def get_total_rating(matchData, plyrPubKey):
        totalRating = 0
        for match in matchData:
            totalRating += helper.get_rating(match['matchData'], np.where(np.asarray(match['plyrAddrList']) == plyrPubKey)[0][0])
        return total_rating

    def is_any_MVP(matchData, plyrPubKey):
        for match in matchData:
            if plyrPubKey == match['winnerAddr']: return True
        return False

    def broadcastResult(nodes, chain):
        for node in nodes:
            print(f"broadcasting...current node: {node}")
            res = requests.post(f"http://{node}/chain/write", json={"chain": chain})
            print(res.text)
        return

    def get_target_rating(matchesData, plyrPubKey, difficulty):
        total_rating = 0
        for match in matchesData:
            plyrIndex = np.where(np.asarray(match['plyrAddrList']) == plyrPubKey)[0]
            if len(plyrIndex) == 0: return -1
            plyrIndex = plyrIndex[0]
            rating, dump = get_rating(match, plyrIndex)
            total_rating += rating
        return (total_rating / len(matchesData)) * difficulty


class Blockchain:
    # longest chain wins because player wants their data asap, so they will agree
    def __init__(self):
        self.chain = []
        self.current_matches = []
        self.current_target = 0
        self.difficulty = 5
        self.myPubKey = ""
        self.nodes = set()

        # import first 500 matches, assume 50 players (requirement to become a miner = played 10 matches)
        if not os.path.isfile(f"{args.nodeID}.blockchain"):
            self.current_target = -1
            with open("genesis_block.data", "r") as f:
                data = json.loads(f.read())
                for i in data: self.new_match(i)
            proof_of_play(genesis=True)
        else:
            with open(f"{args.fileLoc}", "r") as f:
                data = json.loads(f.read())
                self.chain = data["chain"]
                self.current_matches = data["current_matches"]
                self.current_target = data["current_target"]
                self.difficulty = data["difficulty"]
                self.myPubKey = data["myPubKey"]
                self.nodes = data["nodes"]
        saveState()

    def register_node(self, address):
        self.nodes.add(address)

    def proof_of_play(self,genesis=False):
        # find if current matches score > target
        # find if there exists one with this player as mvp
        isMVP = False
        totalRating = 0
        totalRating = helper.get_total_rating(self.current_matches, self.myPubKey)
        isMVP = is_any_MVP(matchData, self.myPubKey)
        print(f"Target: {self.current_target}, Current Total Rating: {totalRating}, Is MVP: {isMVP}.")
        if totalRating < target or not isMVP: return
        print(f"Target reached, broadcasting results...")
        self.new_block(totalRating, 1, genesis=True)
        helper.broadcastResult()
        return

    def valid_match(self):
        # go to all players addr, valid pub pri key

        return

    def valid_PoP(self, all_current_matches, pubKey, target):
        # check if total rating > target
        if helper.get_total_rating(all_current_matches, pubKey) < target: return False
        else: return True

    def new_block(self, plyrProof, pubKey, previous_hash=None, genesis=False):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'matches': self.current_matches,
            'plyrProof': plyrProof,
            'popTarget': self.current_target,
            'previous_hash': previous_hash or self.hash(self.last_block())
        }

        self.current_matches = []
        if not genesis:
            self.target = get_target_rating(self.last_block().current_matches, self.myPubKey)
        else:
            self.target = get_target_rating(block.matches, self.myPubKey)
        self.chain.append(block)
        print("new block created.")
        if args.saveState: saveState()
        return block

    def new_match(self, match):
        self.current_matches.append({
            'plyrAddrList': match['plyrAddrList'],
            'winnerAddr': match['winnerAddr'],
            'matchData': match['matchData']
        })
        if args.saveState: saveState()
        proof_of_play()
        return self.last_block['index'] + 1

    def valid_chain(self, chain):
        # valid matches too
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_PoP(block.current_matches):
                return False

            last_block = block
            current_index += 1
        
        return True

    def resolve_conflict(self, chain):
        if len(chain) > len(self.chain):
            if self.valid_chain(self, chain):
                self.chain = chain
            
    def saveState(self):
        data = json.dumps({"chain": self.chain, "current_matches": self.current_matches, "current_target": self.current_target, "difficulty": self.difficulty, "myPubKey": self.myPubKey, "nodes": self.nodes})
        with open(f"{args.nodeID}.blockchain", "w") as f:
            f.write(data)
        return

    @staticmethod
    def hash(block):
        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]


def init_keyPair(blockchain):
    if not os.path.isfile(f"{args.keyLoc}/{args.nodeID}.pubKey") or not os.path.isfile(f"{args.keyLoc}/{args.nodeID}.priKey"):
        print("no key pair found, non-valid player.")
    else:
        with open(f"{args.keyLoc}/{args.nodeID}.pubKey", "rb") as pubKeyF:
            blockchain.pubKey = pubKeyF.read()
    return


myPort = 9000
if args.bootstrapIP is not None: bootstrapNode = args.bootstrapIP
else: bootstrapNode = None
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')

class config:
    knownNodesFile = f"knownNodes{args.nodeID}.appData"

######### blockchain host ###########

blockchain = Blockchain()
@app.route('/status', methods=['GET'])
def return_status():
    return json.dumps({'status': 'ok'}), 200

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

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return json.dumps(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    content = json.loads(request.data)
    nodes = content["nodes"]
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)

    with open(config.knownNodesFile, 'w') as knownNode:
        serialize_node = ""
        for node in blockchain.nodes: serialize_node += f"{node} "
        knownNode.write(serialize_node[:-1])

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return json.dumps(response), 201

@app.route('/nodes/retrieve', methods=['GET'])
def return_nodes():
    print(blockchain.nodes)
    print(list(blockchain.nodes))
    return json.dumps({"nodes": list(blockchain.nodes)}), 200

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
    if os.path.isfile(config.knownNodesFile):
        with open(config.knownNodesFile, 'r') as content:
            addrs = content.read().split(" ")
            for addr in addrs: blockchain.nodes.add(addr)
        print(f"nodes {str(addrs)} has been added.")
    else:
        print("no known nodes needed to be added.")

    if bootstrapNode is not None:
        content = requests.get(f'http://{bootstrapNode}/nodes/retrieve').text
        requested_nodes = json.loads(content)['nodes']
        for addr in requested_nodes: blockchain.nodes.add(addr)
        print(f"nodes {str(requested_nodes)} has been added from bootstrap node.")
    return

def setup_app(app):
    load_nodes()
    return

def run_server():
    setup_app(app)
    app.run(host='0.0.0.0', port=myPort)

def main():
    global blockchain
    init_keyPair(blockchain)
    # Process(target=run_server, args=()).start()
    run_server()

if __name__ == "__main__":
    main()