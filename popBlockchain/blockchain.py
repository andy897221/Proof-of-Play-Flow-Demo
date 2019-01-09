import hashlib
import json
from time import time
import time
import os
import pickle

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

from key import *

class Blockchain:
    # longest chain wins because player wants their data asap, so they will agree
    def __init__(self, args, helper):
        self.chain = []
        self.current_matches = []
        self.current_target = 0
        self.current_rating = 0
        self.difficulty = 5
        self.nodes = dict()
        self.args = args
        self.helper = helper

        # import first 500 matches, assume 50 players (requirement to become a miner = played 10 matches)
        if not os.path.isfile(f"{self.args.fileLoc}/{self.args.nodeID}.blockchain"):
            self.current_target = -1
            with open(f"{self.args.keyLoc}/{self.args.nodeID}.pubKey", "r") as f:
                key.pubKey = f.read()
            with open(f"{self.args.fileLoc}/genesis_block.data", "r") as f:
                data = json.loads(f.read())
                for i in data: self.new_match(i, genesis=True)
            self.proof_of_play(genesis=True)
        else:
            with open(f"{self.args.fileLoc}/{self.args.nodeID}.blockchain", "r") as f:
                data = json.loads(f.read())
                self.chain = data["chain"]
                self.current_matches = data["current_matches"]
                self.current_target = data["current_target"]
                self.current_rating = data["current_rating"]
                self.difficulty = data["difficulty"]
                key.pubKey = data["myPubKey"].encode("utf-8")
                self.nodes = self._nodeStrToBytes(data["nodes"])
        if self.args.saveState: self.saveState()

    def register_node(self, pubKey, addr):
        self.nodes[pubKey] = addr
        return

    def proof_of_play(self,genesis=False):
        # find if current matches score > target
        # find if there exists one with this player as mvp
        isMVP = False
        self.current_rating = self.helper.get_total_rating(self.current_matches, key.pubKey)
        isMVP = self.helper.is_any_MVP(self.current_matches, key.pubKey)
        print(f"Target: {self.current_target}, Current Total Rating: {self.current_rating}, Is MVP: {isMVP}.")
        if (self.current_rating < self.current_target) or ((not isMVP) and (not genesis)): return
        print("Target reached.")
        self.new_block(genesis=genesis)
        print("Broadcasting results...")
        self.helper.broadcastResult(self.nodes, self.chain)
        # the first genesis process is correct, another process of pop comes up before web hosting, whats that?
        return

    def valid_match(self):
        # go to all players addr, valid pub pri key

        return

    def valid_PoP(self, all_current_matches, pubKey, target):
        # check if total rating > target
        if self.helper.get_total_rating(all_current_matches, pubKey) < target: return False
        else: return True

    def new_block_init(self, matches, genesis=False, block={}):
        self.current_matches = matches
        if not genesis:
            self.current_target = self.helper.get_target_rating(self.last_block().current_matches, key.pubKey, self.difficulty)
        else:
            self.current_target = self.helper.get_target_rating(block["matches"], key.pubKey, self.difficulty)
        self.current_rating = self.helper.get_total_rating(self.current_matches, key.pubKey)
        return

    def new_block(self, genesis=False):
        if genesis: previousHash = SHA256.new("1".encode("utf-8"))
        else: previousHash = self.hash(self.last_block())
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'matches': self.current_matches,
            'popTarget': self.current_target,
            'popRating': self.current_rating,
            'difficulty': self.difficulty,
            'plyrPubKey': key.pubKey,
            # can the state of sign restart from save?
            'signed_previousHash': pkcs1_15.new(RSA.import_key(key.priKey)).sign(previousHash),
            'previousHash': previousHash.hexdigest()
        }
        self.new_block_init(matches=[], genesis=genesis, block=block)
        self.chain.append(block)
        print(f"new block created. next target: {self.current_target}")
        if self.args.saveState: self.saveState()
        proof_of_play()
        return block

    def new_match(self, match, genesis=False):
        self.current_matches.append({
            'plyrAddrList': match['plyrAddrList'],
            'winnerAddr': match['winnerAddr'],
            'matchData': match['matchData']
        })
        if self.args.saveState: self.saveState()
        # print('new match has been added. winner: ...{}'.format(self.current_matches[-1]["winnerAddr"].split("\n")[1][-10:-1]))
        if not genesis: self.proof_of_play()
        if genesis: return 1
        return self.last_block['index'] + 1

    def valid_chain(self, chain):
        # validate matches too
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block).hexdigest():
                return False

            if not self.valid_PoP(block.current_matches):
                return False

            # validate block writer
            try:
                pkcs1_15.new(RSA.import_key(block['plyrPubKey'])).verify(
                    self.hash(last_block), block["signed_previousHash"]
                )
            except (ValueError, TypeError):
                return False

            last_block = block
            current_index += 1
        
        return True

    def replace_chain(self, chain):
        my_matches_val = [matches for block in self.chain for matches in block.matches]
        my_matches_id = [matches['matchData']['match_id'] for matches in my_matches_val]
        other_matches_val = [matches for block in chain for matches in block.matches]
        other_matches_id = [matches['matchData']['match_id'] for matches in other_matches_val]

        my_matches = dict()
        for matches in range(0, len(my_matches_id)):
            my_matches[my_matches_id[matches]] = my_matches_val[matches]

        other_matches = dict()
        for matches in range(0, len(other_matches_id)):
            other_matches[other_matches_id[matches]] = other_matches_val[matches]

        unprocessed_matches = []
        for key, item in my_matches.item():
            if key not in other_matches: unprocessed_matches += [item]

        self.chain = chain
        self.new_block_init(matches=unprocessed_matches)
        return

    def resolve_conflict(self, chain):
        if len(chain) > len(self.chain):
            if self.valid_chain(self, chain):
                self.replace_chain(chain)
            
    def saveState(self):
        convertedNodes = self._nodeBytesToStr(self.nodes)
        data = json.dumps({"chain": self.chain, "current_matches": self.current_matches, "current_target": self.current_target, "current_rating": self.current_rating, "difficulty": self.difficulty, "myPubKey": key.pubKey.decode('utf-8'), "nodes": convertedNodes})
        with open(f"{self.args.fileLoc}/{self.args.nodeID}.blockchain", "w") as f:
            f.write(data)
        return

    def _nodeBytesToStr(self, nodes):
        convertedNodes = dict()
        for node in nodes: convertedNodes[node.decode('utf-8')] = nodes[node]
        return convertedNodes

    def _nodeStrToBytes(self, nodes):
        convertedNodes = dict()
        for node in nodes: convertedNodes[node.encode('utf-8')] = nodes[node]
        return convertedNodes

    @staticmethod
    def hash(block):
        block_str = json.dumps(block, sort_keys=True).encode('utf-8')
        return SHA256.new(block_str)

    @property
    def last_block(self):
        return self.chain[-1]