import hashlib, time, json, hmac, os
from dataclasses import dataclass, field, asdict
from typing import List

MAX_SUPPLY = 42000000.0

class Wallet:
    def __init__(self, name):
        self.name = name
        self.private_key = os.urandom(32).hex()
        self.public_key = hashlib.sha256(self.private_key.encode()).hexdigest()[:20]

    def sign_transaction(self, receiver_public_key, amount):
        message = f"{self.public_key}{receiver_public_key}{amount}".encode()
        signature = hmac.new(self.private_key.encode(), message, hashlib.sha256).hexdigest()
        return signature

@dataclass
class Transaction:
    sender_public_key: str
    receiver_public_key: str
    amount: float
    signature: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "sender_public_key": self.sender_public_key,
            "receiver_public_key": self.receiver_public_key,
            "amount": self.amount,
            "timestamp": self.timestamp
        }

@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Transaction]
    prev_hash: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self):
        payload = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "txs": [t.to_dict() for t in self.transactions],
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

class SuavaChain:
    DIFFICULTY = 4 

    def __init__(self):
        self.chain: List[Block] = [self._genesis()]
        self.mempool: List[Transaction] = []

    def _genesis(self):
        b = Block(0, time.time(), [], "0"*64)
        b.hash = b.compute_hash()
        return b

    def get_balance(self, public_key):
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender_public_key == public_key:
                    balance -= tx.amount
                if tx.receiver_public_key == public_key:
                    balance += tx.amount
        return balance

    def add_tx(self, tx: Transaction):
        sender_balance = self.get_balance(tx.sender_public_key)
        if sender_balance < tx.amount and tx.sender_public_key != "00000000000000000000":
            return
        if tx.sender_public_key == "00000000000000000000": 
            if tx.amount > MAX_SUPPLY:
                return
        self.mempool.append(tx)

    def mine_block(self):
        prev = self.chain[-1]
        block = Block(len(self.chain), time.time(), self.mempool[:], prev.hash)
        target = "0" * self.DIFFICULTY
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        self.chain.append(block)
        self.mempool = []
        return block

    def save_to_disk(self, filename="blockchain.json"):
        data = [asdict(block) for block in self.chain]
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)