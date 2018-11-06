import time, json
from Crypto.Hash import SHA256
from urllib.parse import urlparse
from textwrap import dedent
from uuid import uuid4
from flask import Flask
import PoPConn

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.current_transactions = []
        self.chain.append(block)
        return block
    
    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'virtualCoins': amount
        })
        return self.last_block['index']+1

    @staticmethod
    def hash(block):
        blockStr = json.dumps(block, sort_keys=True).encode()
        return SHA256.new(blockStr).hexdigest()

    @property
    def last_block(self):
        pass


