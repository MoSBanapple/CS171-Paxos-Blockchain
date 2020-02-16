# CS171-Paxos-Blockchain

Class project to create distributed system that makes and records transactions between different clients. Uses Paxos agreement protocols and blockchain.

Setup: Place server.py in all machines where you wish to run the servers, and client.py in the machine where you want to run the client. Place config.txt in all involved machines. Start servers with "python3 server.py (server number)", with (server number) being 0-4. Start client with "client.py". config.txt lists the address and port for servers 0-4, with each server corresponding to a line.

Commands:

"transfer (amount) (sender) (receiver)" sends a transaction request for the sender to send the receiver the given amount. This is send to the sending server (if it is down, it's sent to the next server sequentially).

"blockchain (server)" prints the blockchain as perceived by the target server.

"balance (server)" prints the current balance as perceived by the target server.

"set (server)" prints the unprocessed transactions currently held at the target server.

To partition, go to a server process and input the servers you wish that server to be able to connect to. For example, if you want server 0 to only be able to connect to servers 1 and 2, go to the server 0 process and input "1 2".
