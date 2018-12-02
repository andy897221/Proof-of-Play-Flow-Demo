import hashlib
import json
from time import time
import time
from urllib.parse import urlparse
from uuid import uuid4
from multiprocessing import Process
import argparse

import requests
from flask import Flask, jsonify, request

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bootstrapIP", type=str, help="ip address of bootstrap node")
args = parser.parse_args()

class Blockchain:
    # longest chain wins because player wants their data asap, so they will agree
    def __init__(self):
        self.chain = []
        self.currernt_game_data = []
        self.current_matches = []
        self.nodes = set()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def proof_of_play(self, all_current_matches):
        # get best match (all data is highest) as seed
        # randomly pick one match from allMatches
        # allMatches should have a probability distribution of sin wave
        return

    def valid_match(self):
        # go to all players addr, valid pub pri key
        return

    def valid_PoP(self, all_current_matches):
        # go through PoP process again
        return

    def new_block(self, plyrProof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'matches': self.current_matches,
            'gameData': self.currernt_game_data,
            'plyrProof': plyrProof, # proof that the block writer is indeed the lottery winner
            'previous_hash': previous_hash
        }

        self.current_matches = []
        self.chain.append(block)
        return block

    def new_match(self, match):
        self.current_matches.append({
            'plyrAddrList': match['plyrAddrList'],
            'winnerAddr': match['winner'],
            'matchData': match['matchData']
        })
        return self.last_block['index'] + 1

    def valid_chain(self, chain):
        # ALSO CHECK IF EACH BLOCK HAS ENOUGH RECORDS!!!!!!!!
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_PoP(block.current_matches):
                return False

            last_block = block
            current_index += 1
        
        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        if new_chain:
            self.chain = new_chain
            return True
        return False
            

    @staticmethod
    def hash(block):
        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]



myPort = 9999
bootstrapNode = args.bootstrapIP
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/status', methods=['GET'])
def return_status():
    return json.dumps({'status': 'ok'}), 200

@app.route('/matches/new', methods=['POST'])
def new_match():
    # add new match
    match = request.get_json()
    required = ['plyrAddrList', 'winnerAddr', 'matchData']
    if not all(k in match for k in required):
        return 'Missing values', 400
    index = blockchain.new_match(match)
    response = {'message': f'match will be added to Block {index}'}
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
    content = request.get_json()
    nodes = content.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)

    knownNode = open('knownNodes.appData', 'w')
    serialize_node = ""
    for node in blockchain.nodes: serialize_node += f"{node} "
    knownNode.write(serialize_node[:-1])
    knownNode.close()

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return json.dumps(response), 201

@app.route('/nodes/retrieve', methods=['GET'])
def return_nodes():
    return json.dumps({"nodes", list(blockchain.nodes)}), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return json.dumps(response), 200

def run_server():
    app.run(host='0.0.0.0', port=myPort)

def proof_of_play():
    return

def load_nodes():
    curStatusCode = requests.codes.im_a_teapot
    while curStatusCode != requests.codes.ok:
        try:
            curStatusCode = requests.get(f'127.0.0.1:{myPort}/status').status_code
        except Exception:
            pass
        time.sleep(1)
    with open('knownNodes.appData', 'r') as content:
        for addr in content.read().split(" "): blockchain.nodes.add(addr)
    print(f"nodes {blockchain.nodes} has been added.")
    requested_nodes = json.loads(requests.get(bootstrapNode).text)['nodes']
    curStatusCode = requests.codes.im_a_teapot
    while curStatusCode != requests.codes.created:
        try:
            curStatusCode = request.post(f'127.0.0.1{myPort}/register_nodes',
                data = {'nodes': requested_nodes})
        except Exception:
            pass
        time.sleep(1)
    return

def main():
    Process(target=run_server, args=()).start()
    Process(target=load_nodes, args=()).start()
    Process(target=proof_of_play, args=()).start()

if __name__ == "__main__":
    main()