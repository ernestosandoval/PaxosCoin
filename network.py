#!/usr/bin/env python3
import sys
import socket
from threading import Thread
import time
from random import random
import json
import pickle
from ballot import Ballot

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()

class Network:
    def __init__(self, port, numberOfServers, lower, upper):
        self.port = port
        self.numberOfServers = numberOfServers
        self.lower = lower
        self.upper = upper
        self.socket = socket.socket()
        self.socket.bind(("localhost", self.port))
        self.socket.listen(numberOfServers)

    def start(self):
        while True:
            node, address = self.socket.accept()
            message = node.recv(1024)
            message = pickle.loads(message)
            Thread(target=self.handleMessage, args=(message,)).start()
            node.close()

    def handleMessage(self, message):
        # message = (sender, recipient, messageType, arguments)
        wait= (random() * (self.upper-self.lower)) + self.lower
        time.sleep(wait)
        try:
            recipient = socket.socket()
            recipient.connect(('localhost', config['nodes'][message[1]]))
            recipient.send(pickle.dumps(message))
            recipient.close()
            print(f"Server {message[0]} sent {message[2]} {message[3][0]} to {message[1]} after {wait:.2f} second delay")
        except ConnectionRefusedError:
            print(f"Server {message[0]} sent {message[2]} {message[3][0]} to {message[1]} after {wait:.2f} second delay but failed to connect")

if __name__ == '__main__':
    numberOfServers = 5
    lower = 1
    upper = 3

    network = Network(config['network']['port'], numberOfServers, lower, upper)
    network.start()
