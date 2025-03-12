#!/usr/bin/env python3
import sys
import time
from random import random
from threading import Thread
import json
import socket
import pickle
from ballot import Ballot
import block
import hashlib

PREPARE  = "PREPARE "
ACK      = "ACK     "
ACCEPT   = "ACCEPT  "
ACCEPT2  = "ACCEPT2 "
DECISION = "DECISION"
SYNC     = "SYNC    "

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)
config = load_config()

class Node:
    def __init__(self, pid, port, numberOfServers):
        self.pid = pid
        self.numberOfServers = numberOfServers
        self.majority = numberOfServers // 2
        self.maxBallot = Ballot(-1,-1,-1)
        self.acksReceived = 0
        self.accept2Received = 0
        self.acceptBallot = None
        self.acceptValue = None

        self.handle = {
            PREPARE:  self.handlePrepare,
            ACK:      self.handleAck,
            ACCEPT:   self.handleAccept,
            ACCEPT2:  self.handleAccept2,
            DECISION: self.handleDecision,
            SYNC:     self.handleSync
        }
        self.port = port
        self.socket = socket.socket()
        self.socket.bind(('localhost', self.port))
        self.socket.listen(numberOfServers)

        self.listenerThread = Thread(target=self.recv, daemon=True)
        self.listenerThread.start()

        self.blockchain = []
        self.wallets = {}
        for n in config['nodes']:
            self.wallets[n] = 100
        self.currentTransactions = []

    def __repr__(self) -> str:
        return f"Server {self.pid}"

    def sendToNode(self, sender, recipient, messageType, arguments):
        print(f"Server {sender} sending  {messageType} {arguments[0]} to   server {recipient}")

        network = socket.socket()
        network.connect(('localhost', config['network']['port']))
        network.send(pickle.dumps((sender, recipient, messageType, arguments)))
        network.close()

    def recv(self):
        while True:
            # message = (sender, recipient, messageType, arguments)
            client, address = self.socket.accept()
            message = client.recv(1024)
            message = pickle.loads(message)
            print(f"Server {message[1]} received {message[2]} {message[3][0]} from server {message[0]}")
            self.handle[message[2]](*message[3])

    def hash(self, block):
        concatenation = str(block.depth) + block.prev_hash + block.nonce + str(block.tx)
        return hashlib.sha256(concatenation.encode()).hexdigest()

    def mine(self):
        b = block.block()
        if (self.blockchain):
            b.prev_hash = self.hash(self.blockchain[-1])
            b.depth = self.blockchain[-1].depth + 1
        b.tx = self.currentTransactions[:2]
        b.nonce = self.pid + b.nonce
        while(self.hash(b)[:3] != "000"):
            b.nonce = b.nonce[0] + str(int(b.nonce[1:])+1)
        return b

    def printBlockchain(self):
        for block in self.blockchain:
            print(block)
        return
            
    def printBalance(self):
        print(f"Server {self.pid}: {self.wallets[self.pid]}")
        return
        
    def printSet(self):
        print(self.currentTransactions)
        return
    
    def moneyTransfer(self):
        T = input("Enter a transaction: ").split()
        try:
            assert len(T) == 3
        except AssertionError:
            print("Expected three arguments. Usage: server1 server2 amount")
            return
        if T[0] not in config['nodes']:
            print(f"{T[0]} is not a valid server. Usage: server1 server2 amount")
            return
        if T[1] not in config['nodes']:
            print(f"{T[1]} is not a valid server. Usage: server1 server2 amount")
            return
        try:
            int(T[2])
        except ValueError:
            print(f"{T[2]} is not a valid amount. Usage: server1 server2 amount")
            return

        self.currentTransactions.append(T)
        if ((len(self.currentTransactions) == 2) and (not self.acceptBallot)):
            self.initiatePaxos()
        return
    
    def initiatePaxos(self):
        self.acksReceived = 0
        self.accept2Received = 0

        self.acceptValue = self.mine()
        self.acceptBallot = Ballot(self.maxBallot.n+1, self.pid, self.acceptValue.depth)
        
        self.maxBallot = self.acceptBallot

        for n in config['nodes']:
            if n != self.pid:
                self.sendToNode(self.pid, n, PREPARE, (self.acceptBallot,))
        return

    def handlePrepare(self, bal):
        if bal.depth < len(self.blockchain):
            # bal.pid is proposing a block with depth lower than our latest one
            # we must inform it that a decision has been made already
            self.sendToNode(self.pid, bal.pid, SYNC, (self.maxBallot, self.blockchain))
            return
        if bal < self.maxBallot:
            return
        # promise not to accept ballots smaller than bal in the future
        self.maxBallot = bal
        self.acksReceived = 0
        self.accept2Received = 0
        # tell the leader about the last accepted value and what ballot it was accepted in, if any
        self.sendToNode(self.pid, bal.pid, ACK, (bal, self.acceptBallot, self.acceptValue))
        return

    def handleAck(self, bal, acceptBallot, acceptValue):
        if bal < self.maxBallot or self.acksReceived >= self.majority:
            return
        if acceptBallot:
            if not self.acceptBallot or (acceptBallot > self.acceptBallot):
                self.acceptBallot = acceptBallot
                self.acceptValue = acceptValue
        self.acksReceived += 1
        if self.acksReceived >= self.majority:
            for n in config['nodes']:
                if n != self.pid:
                    self.sendToNode(self.pid, n, ACCEPT, (bal, self.acceptValue))
        return

    def handleAccept(self, bal, block):
        # this should actually return ACCEPT2(bal, block) if this node has accepted this block before in the past
        if bal < self.maxBallot or self.acceptBallot:
            return
        self.maxBallot = bal
        self.acceptBallot = bal
        self.acceptValue = block
        self.sendToNode(self.pid, bal.pid, ACCEPT2, (bal, block))
        return

    def handleAccept2(self, bal, block):
        if bal < self.maxBallot or not self.acceptBallot:
            return
        self.accept2Received += 1
        if self.accept2Received >= self.majority:
            print("foo")
            self.accept2Received = 0
            for n in config['nodes']:
                if n != self.pid:
                    self.sendToNode(self.pid, n, DECISION, (bal, self.blockchain + [block]))
            self.handleDecision(bal, self.blockchain + [block])
        return

    def handleDecision(self, bal, blockchain):
        self.blockchain = blockchain
        for t in blockchain[-1].tx:
            self.wallets[t[0]] -= int(t[2])
            self.wallets[t[1]] += int(t[2])
        if self.blockchain[-1].nonce[0] == self.pid:
            self.currentTransactions = self.currentTransactions[2:]
        self.acceptBallot = None
        self.acceptValue = None
        print(f"Server {self.pid} decided")
        if (len(self.currentTransactions) >= 2):
            self.initiatePaxos()

    def handleSync(self, bal, blockchain):
        # if we received this then we sent a stale prepare message (lower depth value)
        if self.maxBallot < bal:
            self.maxBallot = bal
            self.blockchain = blockchain
        return

    def start(self):
        fns = {"1": self.moneyTransfer, "2": self.printBlockchain, "3": self.printBalance, "4": self.printSet}
        while(True):
            try: 
                com = input("Enter 1 (moneyTransfer), 2 (printBlockchain), 3 (printBalance) or 4 (printSet): ")
            except:
                print("Goodbye!")
                return
            try:
                fns[com]()
            except:
                if (com and (not com.isspace())):
                    print("input should be 1, 2, 3 or 4")

if __name__ == '__main__':
    try:
        serverID = sys.argv[1]
    except IndexError:
        print("Error: Missing argument. Usage: ./server serverID")
        sys.exit(1)  # Exit with a non-zero status to indicate an error
    try:
        port = config['nodes'][serverID]
    except KeyError:
        print(f"{serverID} is not a valid server ID")
        sys.exit(1)  # Exit with a non-zero status to indicate an error    

    numberOfServers = len(config['nodes'])

    node = Node(serverID, port, numberOfServers)
    try:
        node.start()
    except KeyboardInterrupt:
        node.close()
    print("Bye!")