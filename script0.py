import hashlib
import json
from time import time
from typing import Dict, List, Any
import os
import socket
import threading
import pickle

class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], timestamp: float, previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> Dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, block_dict: Dict):
        block = cls(
            block_dict["index"],
            block_dict["transactions"],
            block_dict["timestamp"],
            block_dict["previous_hash"]
        )
        block.hash = block_dict["hash"]
        return block

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []

    def create_genesis_block(self) -> Block:
        return Block(0, [], time(), "0")

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block):
        block.previous_hash = self.get_latest_block().hash
        block.hash = block.calculate_hash()
        self.chain.append(block)

    def add_transaction(self, transaction: Dict[str, Any]):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        block = Block(len(self.chain), self.pending_transactions, time(), self.get_latest_block().hash)
        self.add_block(block)
        self.pending_transactions = []

    def to_dict(self) -> Dict:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": self.pending_transactions
        }

    @classmethod
    def from_dict(cls, blockchain_dict: Dict):
        blockchain = cls()
        blockchain.chain = [Block.from_dict(block_dict) for block_dict in blockchain_dict["chain"]]
        blockchain.pending_transactions = blockchain_dict["pending_transactions"]
        return blockchain

class CustomerData:
    def __init__(self, port: int):
        self.blockchain = Blockchain()
        self.access_levels = {
            "public": ["name", "age"],
            "private": ["address", "skills", "education", "work_experience"],
            "admin": ["all"]
        }
        self.port = port
        self.peers = set()

    def add_customer(self, customer_data: Dict[str, Any], access_level: str):
        if access_level not in self.access_levels:
            raise ValueError("Invalid access level")

        transaction = {
            "type": "add_customer",
            "data": customer_data,
            "access_level": access_level
        }
        self.blockchain.add_transaction(transaction)
        self.blockchain.mine_pending_transactions()
        self.broadcast_blockchain()

    def update_customer(self, customer_name: str, updated_data: Dict[str, Any], access_level: str):
        if access_level not in self.access_levels:
            raise ValueError("Invalid access level")

        transaction = {
            "type": "update_customer",
            "name": customer_name,
            "data": updated_data,
            "access_level": access_level
        }
        self.blockchain.add_transaction(transaction)
        self.blockchain.mine_pending_transactions()
        self.broadcast_blockchain()

    def get_customer_data(self, customer_name: str, requester_access_level: str) -> Dict[str, Any]:
        allowed_fields = self.access_levels.get(requester_access_level, [])
        if "all" in allowed_fields:
            allowed_fields = list(set().union(*self.access_levels.values()))

        customer_data = {}
        for block in reversed(self.blockchain.chain):
            for transaction in reversed(block.transactions):
                if transaction["type"] == "add_customer" and transaction["data"]["name"] == customer_name:
                    customer_data = transaction["data"]
                elif transaction["type"] == "update_customer" and transaction["name"] == customer_name:
                    customer_data.update(transaction["data"])

        return {k: v for k, v in customer_data.items() if k in allowed_fields}

    def save_to_file(self, filename: str):
        data = {
            "blockchain": self.blockchain.to_dict(),
            "access_levels": self.access_levels
        }
        with open(filename, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load_from_file(cls, filename: str, port: int):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        customer_data = cls(port)
        customer_data.blockchain = Blockchain.from_dict(data["blockchain"])
        customer_data.access_levels = data["access_levels"]
        return customer_data

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', self.port))
        server.listen()

        print(f"Server listening on port {self.port}")

        while True:
            client, address = server.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client,))
            client_handler.start()

    def handle_client(self, client):
        try:
            data = client.recv(4096)
            message = pickle.loads(data)

            if message['type'] == 'get_blockchain':
                response = {
                    'type': 'blockchain',
                    'data': self.blockchain.to_dict()
                }
                client.send(pickle.dumps(response))
            elif message['type'] == 'blockchain':
                received_blockchain = Blockchain.from_dict(message['data'])
                self.resolve_conflicts(received_blockchain)

            client.close()
        except Exception as e:
            print(f"Error handling client: {e}")

    def broadcast_blockchain(self):
        for peer in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(peer)
                    message = {
                        'type': 'blockchain',
                        'data': self.blockchain.to_dict()
                    }
                    s.send(pickle.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to peer {peer}: {e}")

    def resolve_conflicts(self, new_blockchain: Blockchain):
        if len(new_blockchain.chain) > len(self.blockchain.chain):
            self.blockchain = new_blockchain
            print("Blockchain updated from peer")

    def add_peer(self, host: str, port: int):
        self.peers.add((host, port))

# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    cd = CustomerData(port)

    # Start the server in a separate thread
    server_thread = threading.Thread(target=cd.start_server)
    server_thread.start()

    while True:
        command = input("Enter command (add/update/get/addpeer/exit): ")

        if command == "add":
            name = input("Enter name: ")
            age = int(input("Enter age: "))
            address = input("Enter address: ")
            skills = input("Enter skills (comma-separated): ").split(',')
            education = input("Enter education (comma-separated): ").split(',')
            work_experience = input("Enter work experience: ")
            access_level = input("Enter access level (public/private/admin): ")

            customer_data = {
                "name": name,
                "age": age,
                "address": address,
                "skills": skills,
                "education": education,
                "work_experience": work_experience
            }
            cd.add_customer(customer_data, access_level)

        elif command == "update":
            name = input("Enter name of customer to update: ")
            field = input("Enter field to update: ")
            value = input("Enter new value: ")
            access_level = input("Enter access level (public/private/admin): ")

            cd.update_customer(name, {field: value}, access_level)

        elif command == "get":
            name = input("Enter name of customer to retrieve: ")
            access_level = input("Enter your access level (public/private/admin): ")

            print(cd.get_customer_data(name, access_level))

        elif command == "addpeer":
            host = input("Enter peer host: ")
            peer_port = int(input("Enter peer port: "))
            cd.add_peer(host, peer_port)

        elif command == "exit":
            break

        else:
            print("Invalid command")

    print("Exiting...")
    sys.exit(0)