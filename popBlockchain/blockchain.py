import json
from time import time
import time
import os
import pickle

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

class Blockchain:
    # longest chain wins because player wants their data asap, so they will agree
    def __init__(self, fileLoc, nodeID, saveState, helper, key, auto_broadcast):
        self.chain = []
        self.current_matches = []
        self.current_target = 0
        self.current_rating = 0
        self.difficulty = 5
        self.nodes = dict()
        self.fileLoc = fileLoc
        self.nodeID = nodeID
        self.isSaving = saveState
        self.helper = helper
        self.key = key
        self.auto_broadcast = auto_broadcast

        # import first 500 matches, assume 50 players (requirement to become a miner = played 10 matches)
        if not os.path.isfile(f"{self.fileLoc}/{self.nodeID}.blockchain"):
            self.current_target = -1
            with open(f"{self.fileLoc}/genesis_block.data", "rb") as f:
                data = pickle.loads(f.read())
                for i in data: self.new_match(i, genesis=True)
            self.proof_of_play(genesis=True)
        else:
            with open(f"{self.fileLoc}/{self.nodeID}.blockchain", "rb") as f:
                data = pickle.loads(f.read())
                self.chain = data["chain"]
                self.current_matches = data["current_matches"]
                self.current_target = data["current_target"]
                self.current_rating = data["current_rating"]
                self.difficulty = data["difficulty"]
                self.nodes = data["nodes"]
        if self.isSaving: self.saveState()

    def register_node(self, pubKey, addr):
        # print(pubKey, addr)
        self.nodes[pubKey] = addr
        if self.isSaving: self.saveState()
        return

    def proof_of_play(self,genesis=False):
        # find if current matches score > target
        # find if there exists one with this player as mvp
        self.current_rating = self.helper.get_total_rating(self.current_matches, self.key.pubKey)
        isMVP = self.helper.is_any_MVP(self.current_matches, self.key.pubKey)
        print(f"Target: {self.current_target}, Current Total Rating: {self.current_rating}, Is MVP: {isMVP}.")
        if (self.current_rating < self.current_target) or ((not isMVP) and (not genesis)): return
        print("Target reached.")
        self.new_block(genesis=genesis)
        if self.auto_broadcast:
            print("Broadcasting results...")
            self.helper.broadcastResult(self.nodes, self.chain)
        # the first genesis process is correct, another process of pop comes up before web hosting, whats that?
        return

    @staticmethod
    def valid_match(match):
        # print(match)
        signature = match['signature']
        matchData = match['matchData']
        for senderPubKey in signature:
            for receiverPubKey in signature[senderPubKey]:
                try:
                    pkcs1_15.new(RSA.import_key(receiverPubKey)).verify(
                        SHA256.new(pickle.dumps(matchData)), signature[senderPubKey][receiverPubKey]
                    )
                except (ValueError, TypeError):
                    return False
        return True

    def valid_PoP(self, all_current_matches, pubKey, target):
        # check if total rating > target
        if self.helper.get_total_rating(all_current_matches, pubKey) < target: return False
        else: return True

    def new_block_init(self, matches, chain):
        self.current_matches = matches
        self.current_target = self.helper.get_target_rating(chain, self.key.pubKey, self.difficulty)
        self.current_rating = self.helper.get_total_rating(self.current_matches, self.key.pubKey)
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
            'plyrPubKey': self.key.pubKey,
            'signed_previousHash': pkcs1_15.new(RSA.import_key(self.key.priKey)).sign(previousHash),
            'previousHash': previousHash.hexdigest()
        }
        self.chain.append(block)
        self.new_block_init(matches=[], chain=self.chain)
        print(f"new block created. next target: {self.current_target}")
        if self.isSaving: self.saveState()
        self.proof_of_play()
        return block

    def new_match(self, match, genesis=False):
        if not genesis:
            self.current_matches.append({
                'plyrAddrList': match['plyrAddrList'],
                'winnerAddr': match['winnerAddr'],
                'matchData': match['matchData'],
                'signature': match['signature']
            })
        else:
            self.current_matches.append({
                'plyrAddrList': match['plyrAddrList'],
                'winnerAddr': match['winnerAddr'],
                'matchData': match['matchData'],
                'signature': None
            })
        if self.isSaving: self.saveState()
        # print('new match has been added. winner: ...{}'.format(self.current_matches[-1]["winnerAddr"].split("\n")[1][-10:-1]))
        if not genesis: self.proof_of_play()
        if genesis: return 1
        addToBlock = self.last_block()['index'] + 1
        return addToBlock

    def valid_chain(self, chain):
        # validate matches too
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previousHash'] != self.hash(last_block).hexdigest():
                print("previousHash validate failed.")
                return False

            if not self.valid_PoP(block["matches"], block["plyrPubKey"], block["popTarget"]):
                print("PoPTarget validate failed.")
                return False

            # validate block writer
            try:
                pkcs1_15.new(RSA.import_key(block['plyrPubKey'])).verify(
                    self.hash(last_block), block["signed_previousHash"]
                )
            except (ValueError, TypeError):
                print("block writer validate failed.")
                return False

            # validate matchData
            for match in block['matches']:
                res = self.valid_match(match)
                if not res:
                    print("match validate failed.")
                    return False

            last_block = block
            current_index += 1
        
        return True

    def replace_chain(self, chain):
        my_matches_raw = [matches for block in range(1, len(self.chain)) for matches in self.chain[block]["matches"]]
        other_matches_raw = [matches for block in range(1, len(chain)) for matches in chain[block]["matches"]]

        for my_match in range(0, len(my_matches_raw)):
            for other_match in other_matches_raw:
                if my_matches_raw[my_match] == other_match:
                    my_matches_raw[my_match] = None
                    break

        unprocessed_matches = []
        for my_match in my_matches_raw:
            if my_match is not None: unprocessed_matches += [my_match]

        self.chain = chain
        print("chain has replaced, initializing new block properties...")
        self.new_block_init(matches=unprocessed_matches, chain=self.chain)
        self.proof_of_play()

        return

    def resolve_conflict(self, chain):
        if len(chain) > len(self.chain):
            if self.valid_chain(chain):
                self.replace_chain(chain)
                return True
        return False
            
    def saveState(self):
        # signed_preivousHash is bytes, cannot serial json
        data = {"chain": self.chain, "current_matches": self.current_matches, "current_target": self.current_target
            , "current_rating": self.current_rating, "difficulty": self.difficulty, "nodes": self.nodes}
        with open(f"{self.fileLoc}/{self.nodeID}.blockchain", "wb") as f:
            f.write(pickle.dumps(data))
        return

    @staticmethod
    def hash(block):
        block_str = pickle.dumps(sorted(block.items()))
        return SHA256.new(block_str)

    def last_block(self):
        return self.chain[-1]