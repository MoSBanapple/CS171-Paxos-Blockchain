import socket
import time
import random
import sys
from multiprocessing import Process
import threading

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
    
def getAddress(clientNumber):
    if clientNumber < 0 or clientNumber > 4:
        return ("", -1)
    f = open("config.txt", "r")
    output = f.readline().split()
    for i in range(clientNumber):
        output = f.readline().split()
    return (output[0], int(output[1]))
    
 
def handleInput(strInput):
    spl = strInput.split()
    parsed = []
    for i in range(1, len(spl)):
        parsed.append(int(spl[i]))
    target = 0
    if spl[0] == "transfer":
        target = parsed[1]
        if len(spl) < 4:
            print("Invalid input")
            return
    elif spl[0] == "blockchain" or spl[0] == "balance" or spl[0] == "set":
        target = parsed[0]
        if len(spl) < 2:
            print("Invalid input")
            return
    else:
        print("Invalid input")
        return
    s = socket.socket()
    if target < 0 or target > 4:
        print("Invalid input")
        return
    for i in range(5):
        targetAddress = getAddress((target+i)%5)
        try:
            s.connect((targetAddress[0], targetAddress[1] + 100))
            s.send(strInput.encode())
            print(s.recv(1024).decode())
            s.close()
            break
        except:
            print("Client", (target+i)%5, "unavailable")
            
    

while True:
    print("Input command:")
    strInput = input()
    handleInput(strInput)
