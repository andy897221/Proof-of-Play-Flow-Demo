import hashlib
import json
from time import time
import time
import os

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from key import *

class Blockchain:
    # longest chain wins because player wants their data asap, so they will agree
    def __init__(self):
        self.chain = []
        self.current_matches = []
        self.current_target = 0
        self.current_rating = 0
        self.difficulty = 5
        self.nodes = set()

        # import first 500 matches, assume 50 players (requirement to become a miner = played 10 matches)
        if not os.path.isfile(f"{args.fileLoc}/{args.nodeID}.blockchain"):
            self.current_target = -1
            with open(f"{args.keyLoc}/{args.nodeID}.pubKey", "r") as f:
                key.pubKey = f.read()
            with open("genesis_block.data", "r") as f:
                data = json.loads(f.read())
                for i in data: self.new_match(i, genesis=True)
            self.proof_of_play(genesis=True)
        else:
            with open(f"{args.fileLoc}/{args.nodeID}.blockchain", "r") as f:
                data = json.loads(f.read())
                self.chain = data["chain"]
                self.current_matches = data["current_matches"]
                self.current_target = data["current_target"]
                self.current_rating = data["current_rating"]
                self.difficulty = data["difficulty"]
                key.pubKey = data["myPubKey"]
                self.nodes = set(data["nodes"])
        if args.saveState: self.saveState()

    def register_node(self, address):
        self.nodes.add(address)

    def proof_of_play(self,genesis=False):
        # find if current matches score > target
        # find if there exists one with this player as mvp
        isMVP = False
        self.current_rating += helper.get_total_rating(self.current_matches, key.pubKey)
        isMVP = helper.is_any_MVP(self.current_matches, key.pubKey)
        print(f"Target: {self.current_target}, Current Total Rating: {self.current_rating}, Is MVP: {isMVP}.")
        if self.current_rating < self.current_target or not isMVP: return
        print("Target reached.")
        self.new_block(genesis=genesis)
        print("Broadcasting results...")
        helper.broadcastResult(self.nodes, self.chain)
        # the first genesis process is correct, another process of pop comes up before web hosting, whats that?
        return

    def valid_match(self):
        # go to all players addr, valid pub pri key

        return

    def valid_PoP(self, all_current_matches, pubKey, target):
        # check if total rating > target
        if helper.get_total_rating(all_current_matches, pubKey) < target: return False
        else: return True

    def new_block(self, genesis=False):
        if genesis: previousHash = 1
        else: previousHash = self.hash(self.last_block())
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'matches': self.current_matches,
            'popTarget': self.current_target,
            'popRating': self.current_rating,
            'difficulty': self.difficulty,
            'plyrPubKey': key.pubKey,
            'signed_previousHash': pkcs1_15.new(RSA.import_key(key.priKey)).sign(previousHash)
            'previousHash': previousHash
        }
        self.current_matches = []
        if not genesis:
            self.current_target = helper.get_target_rating(self.last_block().current_matches, key.pubKey, self.difficulty)
        else:
            self.current_target = helper.get_target_rating(block["matches"], key.pubKey, self.difficulty)
        self.current_rating = 0
        self.chain.append(block)
        print(f"new block created. next target: {self.current_target}")
        if args.saveState: self.saveState()
        return block

    def new_match(self, match, genesis=False):
        self.current_matches.append({
            'plyrAddrList': match['plyrAddrList'],
            'winnerAddr': match['winnerAddr'],
            'matchData': match['matchData']
        })
        if args.saveState: self.saveState()
        # print('new match has been added. winner: ...{}'.format(self.current_matches[-1]["winnerAddr"].split("\n")[1][-10:-1]))
        if not genesis: self.proof_of_play()
        if genesis: return 1
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
        data = json.dumps({"chain": self.chain, "current_matches": self.current_matches, "current_target": self.current_target, "current_rating": self.current_rating, "difficulty": self.difficulty, "myPubKey": key.pubKey, "nodes": list(self.nodes)})
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