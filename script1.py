import hashlib
import json
from time import time
from typing import Dict, List, Any
import os
import socket
import threading
import pickle
import random
import asyncio
import aiohttp
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], timestamp: float, previous_hash: str, nonce: int = 0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self) -> Dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, block_dict: Dict):
        block = cls(
            block_dict["index"],
            block_dict["transactions"],
            block_dict["timestamp"],
            block_dict["previous_hash"],
            block_dict["nonce"]
        )
        block.hash = block_dict["hash"]
        return block

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 4  # Adjust this to control mining difficulty
        self.mining_reward = 1  # Reward for mining a block

    def create_genesis_block(self) -> Block:
        return Block(0, [], time(), "0")

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block):
        if self.is_valid_new_block(block, self.get_latest_block()):
            self.chain.append(block)
        else:
            raise ValueError("Invalid block")

    def add_transaction(self, transaction: Dict[str, Any], signature: bytes, public_key: rsa.RSAPublicKey):
        if self.verify_transaction(transaction, signature, public_key):
            self.pending_transactions.append(transaction)
        else:
            raise ValueError("Invalid transaction signature")

    def mine_pending_transactions(self, miner_address: str):
        block = Block(len(self.chain), self.pending_transactions, time(), self.get_latest_block().hash)
        block.mine_block(self.difficulty)
        self.add_block(block)
        self.pending_transactions = [
            {"from": "network", "to": miner_address, "amount": self.mining_reward}
        ]

    def is_valid_new_block(self, new_block: Block, previous_block: Block) -> bool:
        if previous_block.index + 1 != new_block.index:
            return False
        if previous_block.hash != new_block.previous_hash:
            return False
        if new_block.calculate_hash() != new_block.hash:
            return False
        return True

    def is_valid_chain(self, chain: List[Block]) -> bool:
        if chain[0].hash != self.create_genesis_block().hash:
            return False

        for i in range(1, len(chain)):
            if not self.is_valid_new_block(chain[i], chain[i-1]):
                return False

        return True

    def verify_transaction(self, transaction: Dict[str, Any], signature: bytes, public_key: rsa.RSAPublicKey) -> bool:
        try:
            public_key.verify(
                signature,
                json.dumps(transaction, sort_keys=True).encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False

    def to_dict(self) -> Dict:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": self.pending_transactions,
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward
        }

    @classmethod
    def from_dict(cls, blockchain_dict: Dict):
        blockchain = cls()
        blockchain.chain = [Block.from_dict(block_dict) for block_dict in blockchain_dict["chain"]]
        blockchain.pending_transactions = blockchain_dict["pending_transactions"]
        blockchain.difficulty = blockchain_dict["difficulty"]
        blockchain.mining_reward = blockchain_dict["mining_reward"]
        return blockchain

class Node:
    def __init__(self, port: int):
        self.blockchain = Blockchain()
        self.port = port
        self.peers = set()
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, 'localhost', self.port)
        print(f"Server listening on port {self.port}")
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        data = await reader.read()
        message = pickle.loads(data)

        if message['type'] == 'get_blockchain':
            response = {
                'type': 'blockchain',
                'data': self.blockchain.to_dict()
            }
            writer.write(pickle.dumps(response))
            await writer.drain()
        elif message['type'] == 'blockchain':
            received_blockchain = Blockchain.from_dict(message['data'])
            self.resolve_conflicts(received_blockchain)
        elif message['type'] == 'new_transaction':
            transaction = message['data']
            signature = message['signature']
            public_key = message['public_key']
            try:
                self.blockchain.add_transaction(transaction, signature, public_key)
                await self.broadcast_transaction(transaction, signature, public_key)
            except ValueError as e:
                print(f"Invalid transaction: {e}")

        writer.close()

    async def broadcast_blockchain(self):
        for peer in self.peers:
            try:
                reader, writer = await asyncio.open_connection(peer[0], peer[1])
                message = {
                    'type': 'blockchain',
                    'data': self.blockchain.to_dict()
                }
                writer.write(pickle.dumps(message))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"Error broadcasting to peer {peer}: {e}")

    async def broadcast_transaction(self, transaction, signature, public_key):
        for peer in self.peers:
            try:
                reader, writer = await asyncio.open_connection(peer[0], peer[1])
                message = {
                    'type': 'new_transaction',
                    'data': transaction,
                    'signature': signature,
                    'public_key': public_key
                }
                writer.write(pickle.dumps(message))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"Error broadcasting transaction to peer {peer}: {e}")

    def resolve_conflicts(self, new_blockchain: Blockchain):
        if len(new_blockchain.chain) > len(self.blockchain.chain) and new_blockchain.is_valid_chain(new_blockchain.chain):
            self.blockchain = new_blockchain
            print("Blockchain updated from peer")

    def add_peer(self, host: str, port: int):
        self.peers.add((host, port))

    def create_transaction(self, recipient: str, amount: float):
        transaction = {
            "from": self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode(),
            "to": recipient,
            "amount": amount,
            "timestamp": time()
        }
        signature = self.private_key.sign(
            json.dumps(transaction, sort_keys=True).encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return transaction, signature

    def mine(self):
        self.blockchain.mine_pending_transactions(
            self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
        )
        asyncio.run(self.broadcast_blockchain())

async def main(port: int):
    node = Node(port)
    await node.start()

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    asyncio.run(main(port))