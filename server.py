import socket
import time
import random
import sys
from hashlib import sha256
from random import random
from multiprocessing import Process
import threading 
#Usage: python3 server.py (client number)

client = int(sys.argv[1])
delay = 3
blockchainFile = "blockchain" + str(client) + ".txt"

storedTransactions = []
ballotNum = (0, 0)
acceptNum = (0, 0)
acceptVal = None
proposedBlock = None
otherClients = [0, 1, 2, 3, 4]
otherClients.remove(client)
receivedVals = []
receivedBals = []
decideCount = 0
timeOutCheck = [True, True]

class Block:
    def __init__(self, dep, prevH, non, trans):
        self.depth = dep
        self.prevHash = prevH
        self.nonce = non
        self.transactions = trans
    
    def toString(self):
        if len(self.transactions) < 2:
            print (self.transactions)
        return str(self.depth) + " " + self.prevHash + " " + self.nonce + " " + self.transactions[0] + " " + self.transactions[1]
        
        
    def isValid(self):
        hash = sha256(self.toString().encode()).hexdigest()
        return (hash[63] == '0' or hash[63] == '1')
    
    def hash(self):
        return sha256(self.toString().encode()).hexdigest()
    
def makeBlock(inputString):
    spl = inputString.split()
    return Block(int(spl[0]), spl[1], spl[2], spl[3:5])
    
def getBlockchain():
    if not blockchainExists():
        startBlockchain()
    f = open(blockchainFile, "r")
    line = f.readline()
    output = []
    while len(line) > 0:
        output.append(makeBlock(line))
        line = f.readline()
    f.close()
    return output
    
def addBlock(inputBlock):
    f = open(blockchainFile, "a")
    f.write(inputBlock.toString() + "\n")
    f.close()
    
def startBlockchain():
    f = open(blockchainFile, "w")
    f.close()
    
def blockchainExists():
    try:
        open(blockchainFile, "r")
        return True
    except:
        return False
        
def getBalance():
    chain = getBlockchain()
    output = [100, 100, 100, 100, 100]
    for block in chain:
        for trans in block.transactions:
            tranSplit = trans.split(",")
            output[int(tranSplit[1])] -= int(tranSplit[0])
            output[int(tranSplit[2])] += int(tranSplit[0])
    return output

def checkTransactions(toTest):
    balance = getBalance()
    for trans in toTest:
        tranSplit = trans.split(",")
        balance[int(tranSplit[1])] -= int(tranSplit[0])
        balance[int(tranSplit[2])] += int(tranSplit[0])
    for i in balance:
        if i < 0:
            return False
    return True

def getAddress(clientNumber):
    if clientNumber < 0 or clientNumber > 4:
        return ("", -1)
    f = open("config.txt", "r")
    output = f.readline().split()
    for i in range(clientNumber):
        output = f.readline().split()
    return (output[0], int(output[1]))


def parseMessage(inputString):
    output = []
    for v in inputString.split():
        output.append(int(v))
    return output
    
def intsToString(input):
    output = ""
    for v in input:
        output += str(v) + " "
    return output

def sendToServer(target, message):
    p2 = threading.Thread(target=sendHelp, args=(target, message,))
    p2.start()

def sendHelp(target, message):
    time.sleep(random()*delay)
    targetAddress = getAddress(target)
    s = socket.socket()
    try:
        s.connect(targetAddress)
        s.send(message.encode())
        s.close()
    except:
        print("Unable to send", message, "to", target)
    print ("Sent", message, "to", target)
    

def mineAndSendBlock():
    global otherClients
    global storedTransactions
    global ballotNum
    global proposedBlock
    while proposedBlock.depth != 0:
        time.sleep(0.1)
    prevHash = "firstBlock"
    toAdd = Block(0, "", "", ["",""])
    while True:
        bc = getBlockchain()
        if len(bc) > 0:
            prevHash = bc[len(bc)-1].hash()
        if len(storedTransactions) < 2:
            return
        if not checkTransactions(storedTransactions[:2]):
            del storedTransactions[:2]
            return
        toAdd = Block(len(bc)+1, prevHash, str(random()), storedTransactions[:2])
        while (not toAdd.isValid()) and len(bc) == len(getBlockchain()):
            toAdd.nonce = str(random())
        if toAdd.isValid() and proposedBlock.depth == 0:
            break
    proposedBlock = toAdd
    del storedTransactions[:2]
    ballotNum = (ballotNum[0]+1, client)
    toSend = "prepare " + str(ballotNum[0]) + " " + str(ballotNum[1]) + " " + str(len(getBlockchain()))
    for targetClient in otherClients:
        sendToServer(targetClient, toSend)
    startTimeout(0)

def listenToClient(socketNum):
    global storedTransactions
    s = socket.socket()
    s.bind(('', socketNum))
    s.listen(5)
    while True:
        c, addr = s.accept()
        message = c.recv(1024).decode()
        message_spl = message.split()
        if message_spl[0] == "transfer":
            output = message_spl[1] + "," + message_spl[2] + "," + message_spl[3]
            c.send("Transaction added".encode())
            storedTransactions.append(output)
            if len(storedTransactions) >= 2:
                p = threading.Thread(target = mineAndSendBlock)
                p.start()
        elif message_spl[0] == "blockchain":
            bc = getBlockchain()
            output = ""
            for block in bc:
                output += block.toString() + "\n"
            c.send(output.encode())
        elif message_spl[0] == "balance":
            bal = getBalance()
            output = ""
            for i in range(len(bal)):
                output += "Client " + str(i) + ": $" + str(bal[i]) + "\n"
            c.send(output.encode())
        elif message_spl[0] == "set":
            toSend = ""
            for t in storedTransactions:
                toSend += t + "\n"
            c.send(toSend.encode())
        c.close()

def startTimeout(timer):
    #i = 2
    p2 = threading.Thread(target=timeoutHelper, args=(timer,))
    p2.start()

def timeoutHelper(timer):
    global storedTransactions
    global proposedBlock
    global timeOutCheck
    global decideCount
    global receivedVals
    global receivedBals
    currentDepth = len(getBlockchain())
    timeOutCheck[timer] = False
    time.sleep(delay*2.5)
    if not timeOutCheck[timer] and len(getBlockchain()) == currentDepth:
        timeOutCheck[timer] = True
        print("Timeout", timer)
        storedTransactions.extend(proposedBlock.transactions)
        proposedBlock = Block(0, "NULL", "NULL", ["NULL", "NULL"])
        decideCount = 0
        receivedVals = []
        receivedBals = []
        if len(storedTransactions) >= 2:
            mineAndSendBlock()

def partition():
    global otherClients
    while True:
        strInput = input()
        otherClients = parseMessage(strInput)
        print("This server can access the following servers:", otherClients)
        

        
        

    
    
if __name__ == '__main__':
    getBlockchain()
    acceptVal = Block(0, "NULL", "NULL", ["NULL", "NULL"])
    proposedBlock = Block(0, "NULL", "NULL", ["NULL", "NULL"])
    selfPort = getAddress(client)[1]
    p2 = threading.Thread(target=listenToClient, args=(selfPort+100,))
    p2.start()
    part = threading.Thread(target=partition)
    part.start()
    s = socket.socket()
    s.bind(('', selfPort))
    s.listen(5)
    while True:
        c, addr = s.accept()
        message = c.recv(1024).decode()
        print("Received", message)
        message_spl = message.split()
        if message_spl[0] == "prepare":
            targetClient = int(message_spl[2])
            if int(message_spl[3]) < len(getBlockchain()):
                output = "backup "
                for b in getBlockchain():
                    output += ":" + b.toString()
                sendToServer(targetClient, output)
                c.close()
                continue
            recBallot = (int(message_spl[1]), int(message_spl[2]))
            if recBallot > ballotNum:
                ballotNum = recBallot
                output = "ack " + str(recBallot[0]) + " " + str(recBallot[1]) + " " + str(acceptNum[0]) + " " + str(acceptNum[1]) + " " + acceptVal.toString() + " " + str(len(getBlockchain()))
                sendToServer(targetClient, output)
        elif message_spl[0] == "ack":
            if int(message_spl[10]) < len(getBlockchain()):
                c.close()
                continue
            recBallot = (int(message_spl[1]), int(message_spl[2]))
            recNum = (int(message_spl[3]), int(message_spl[4]))
            recBlock = Block(int(message_spl[5]), message_spl[6], message_spl[7], [message_spl[8], message_spl[9]])
            receivedBals.append(recNum)
            receivedVals.append(recBlock)
            if len(receivedBals) == 2:
                timeOutCheck[0] = True
                myVal = proposedBlock
                max = receivedBals[0]
                for i in range(len(receivedBals)):
                    if receivedVals[i].depth == 0:
                        continue
                    if receivedBals[i] >= max:
                        myVal = receivedVals[i]
                        max = receivedBals[i]
                output = "accept1 " + str(recBallot[0]) + " " + str(recBallot[1]) + " " + myVal.toString() + " " + str(client)
                for tc in otherClients:
                    sendToServer(tc, output)
                startTimeout(1)
        elif message_spl[0] == "accept1":
            recBal = (int(message_spl[1]), int(message_spl[2]))
            recBlock = Block(int(message_spl[3]), message_spl[4], message_spl[5], [message_spl[6], message_spl[7]])
            recClient = int(message_spl[8])
            if recBlock.depth < len(getBlockchain()) + 1:
                c.close()
                continue
            if recBal >= ballotNum:
                acceptNum = recBal
                acceptVal = recBlock
                output = "accept2 " + str(recBal[0]) + " " + str(recBal[1]) + " " + recBlock.toString()
                sendToServer(recClient, output)
        elif message_spl[0] == "accept2":
            recBal = (int(message_spl[1]), int(message_spl[2]))
            recBlock = Block(int(message_spl[3]), message_spl[4], message_spl[5], [message_spl[6], message_spl[7]])
            if recBlock.depth < len(getBlockchain()) + 1:
                c.close()
                continue
            if recBlock.depth - 1 == len(getBlockchain()):
                decideCount += 1
            if decideCount == 2:
                timeOutCheck[1] = True
                addBlock(recBlock)
                output = "decision " + str(recBal[0]) + " " + str(recBal[1]) + " " + recBlock.toString() + " " + str(client)
                for tc in otherClients:
                    sendToServer(tc, output)
                decideCount = 0
                acceptNum = (0, 0)
                acceptVal = Block(0, "NULL", "NULL", ["NULL", "NULL"])
                ballotNum = (0, 0)
                timeOutCheck = [True, True]
                proposedBlock = Block(0, "NULL", "NULL", ["NULL", "NULL"])
                receivedBals = []
                receivedVals = []
        elif message_spl[0] == "decision":
            recBal = (int(message_spl[1]), int(message_spl[2]))
            recBlock = Block(int(message_spl[3]), message_spl[4], message_spl[5], [message_spl[6], message_spl[7]])
            recClient = int(message_spl[8])
            if recBlock.depth - 1 != len(getBlockchain()):
                sendToServer(recClient, "recover " + str(client))
                c.close()
                continue
            addBlock(recBlock)
            timeOutCheck = [True, True]
            if proposedBlock.depth > 0:
                storedTransactions.extend(proposedBlock.transactions)
                proposedBlock = Block(0, "NULL", "NULL", ["NULL", "NULL"])
                mineAndSendBlock()
            decideCount = 0
            acceptNum = (0, 0)
            acceptVal = Block(0, "NULL", "NULL", ["NULL", "NULL"])
            ballotNum = (0, 0)
            receivedBals = []
            receivedVals = []
        elif message_spl[0] == "recover":
            output = "backup "
            for b in getBlockchain():
                output += ":" + b.toString()
            sendToServer(int(message_spl[1]), output)
        elif message_spl[0] == "backup":
            blockStrings = message.split(":")
            if len(blockStrings) - 1 <= len(getBlockchain()):
                continue
            startBlockchain()
            for bs in range(1, len(blockStrings)):
                addBlock(makeBlock(blockStrings[bs]))
            timeOutCheck = [True, True]
            if proposedBlock.depth > 0:
                storedTransactions.extend(proposedBlock.transactions)
                proposedBlock = Block(0, "NULL", "NULL", ["NULL", "NULL"])
                if len(storedTransactions) >= 2:
                    mineAndSendBlock()
        c.close()
        
        
        
        
                
