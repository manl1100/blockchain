import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request


class Blockchain(object):

    """
    Block chain walk through
    https://hackernoon.com/learn-blockchains-by-building-one-117428612f46.
    """

    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create new block in the chain.

        :param proof: <int> proof from Proof of Work algorihtm
        :param previous_hash: <str> Hash of previous block
        :return: <dict> new block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates new transaction.

        :param sender: <str> Address of sender
        :param recipient: <str> Address of recipient
        :param amount: <int> Amount
        :return: <int> Chain index of block containing transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains 4 leading zeros, where p is the previous p'
         - p is the previous proof, and p' is the new proof

        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof = proof + 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:2] == '00'

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of Block

        :param block: <dict> Block
        :return: <str>
        """

        # Dict must be ordered to prevent messing up the hashs
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():

    # Run the proof of work algorithm to get next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We receive a reward for finding proof
    # Sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new block by adding it to the chain
    block = blockchain.new_block(proof)

    response = {
        'message': 'New block forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    print(values)

    # Check for required fields
    required = ['sender', 'recipient', 'amount']
    if not all(param in values for param in required):
        return 'Missing values', 400

    # Create new Transaction
    index = blockchain.new_transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount'],
    )
    response = {
        'message': f'Transaction will be added to block {index}'
    }
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
