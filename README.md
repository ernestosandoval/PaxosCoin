 # Paxos Coin

This is a simple implementation of the Paxos protocol to achieve consensus in a blockchain network. It simulates a network of five nodes. To start the network, run:
```
./network.py
```
Then for each server node (A, B, C, D, E), open a new shell and run:
```
./paxos serverID
```

Each server node can run the following commands:
 
`moneyTransfer(amount, client1, client2)`: Transfers `amount` of money from `client1` to `client2`.

`printBlockchain`: Print a copy of the blockchain.

`printBalance`: Print the balance of the 5 clients.

`printSet`: Print the set of transactions currently recorded.

The Paxos protocol ensures consensus even with concurrent proposers. It also handles crash failures, ensuring that the system continues to make progress as long as a majority of nodes are operational. Crashed nodes will automatically update their blockchain when they reconnect to the network. 
