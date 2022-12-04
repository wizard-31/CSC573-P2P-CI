"""
Fall 2022 - CSC573
Author: Subramanian Venkataraman <svenka25@ncsu.edu>
"""

#Importing necessary packages
import time
import datetime
import threading
import signal
from socket import *
import re
from collections import defaultdict
import fnmatch

#RESPONSE MESSAGES
respMessages = {200:"200 OK", 400:"400 Bad Request", 404:"404 Not Found", 505:"505 P2P-CI Version Not Supported"}
p2pversion = "P2P-CI/1.0"
supportedversion = "1.0"

#Server Setup
serverListeningPort = 7734
serverAddress = socket.gethostbyname(socket.gethostname())
serverName = socket.gethostname()
serverSocket = socket(AF_INET,SOCK_STREAM)
BUFFER_SIZE = 2048

try:
    serverSocket.bind((serverAddress, serverListeningPort))
    serverSocket.listen(10)
    print("\nServer is ready......")
except error, (value, message):
    print("\nException: while binding the server...")
    print("\nRegistration Stopped. Please try again...")
    serverSocket.close()
    del serverSocket
    exit(message)

#Initial Lists maintained by server
ActiveConnList = [] #Format: "PeerName--PortNumber"
# RFCtoClientMap = {"RFCNumber": [], "RFC Title": [], "Peer_Hostname":[]}
RFCtoClientMap = defaultdict(list) # Format: "{RFCNumber: [Peer_Hostname--RFC Title]}"

def formatConnectionDetail(hostName, portDetail):
    return "{}--{}".format(hostName, portDetail)

def LetTheConnectionsBegin(clientconnSocket, clientAddr):
    global ActiveConnList
    global RFCtoClientMap

    while True:
        clientData = clientconnSocket.recv(BUFFER_SIZE)
        clientData = clientData.decode('utf-8').split("\r\n")

        clientHeader = clientData[0]
        methodName = clientHeader.split()[0]
        hostDetail = clientData[1].split(":")[1].strip()

        if methodName == "ADD":
            rfcDetail = clientHeader.split()[2]
            p2pver = clientHeader.split()[3]
            portDetail = clientData[2].split(":")[1].strip()
            rfcTitle = clientData[3].split(":")[1].strip()
            pattern = hostDetail+"--*"
            try:
                assert p2pver == p2pversion, respMessages[505]
            except AssertionError, e:
                print("\n{}".format(e))
                print("\n Client using unsupported P2P version. Connection closing")
                clientconnSocket.close()            

            if rfcDetail in RFCtoClientMap.keys():
                matching = fnmatch.filter(RFCtoClientMap[rfcDetail], pattern)
                if len(matching) > 0:
                    replyMessage = respMessages[200] + "\r\n\r\n"
                    clientconnSocket.sendall(replyMessage.encode('utf-8'))
                    continue
            
            matching = fnmatch.filter(ActiveConnList, pattern)
            if len(matching) == 0:
                ActiveConnList.append(formatConnectionDetail(hostDetail, portDetail))
            
            RFCtoClientMap[rfcDetail].append(formatConnectionDetail(hostDetail, rfcTitle))
            replyMessage = "{} {} \r\nRFC {} {} {} {}".format(p2pversion, respMessages[200], rfcDetail, rfcTitle, hostDetail, portDetail)
            clientconnSocket.sendall(replyMessage.encode('utf-8'))
            print("\n Added RFC detail from Client to CI")

        elif methodName == "LIST":
            print("\n Print the whole index of RFCs from the server")
            print("\n\n Who has what you wonder?. Here you go")
            for key, value in RFCtoClientMap.items():
                print("\n RFC Number: {} \t --- \t Clients {}".format(key, value))
            print("\n")

        elif methodName ==             

                


            




        











def NowYouSeeMe():
    print("\n\n Active Connection List:")
    for i in range(len(ActiveConnList)):
        peer, port = i.split("-")[0], i.split("-")[1]
        print("\nPeerName:{} \t --- \t RFC Port Number:{}".format(peer, port)
    print("\n")

    print("\n\n Who has what you wonder?. Here you go")
    for key, value in RFCtoClientMap.items():
        print("\n RFC Number: {} \t --- \t Clients {}".format(key, value))
    print("\n")

def handler(recv_signal, frame):
    print("\n\n Toodaloo...")
    exit()

#This is where Server keeps accepting Connections from Peers
signal.signal(signal.SIGINT, handler)
while True:
    clientconnSocket, clientAddr = serverSocket.accept()
    print("\n Connected to client {} with port # {}".format(clientAddr, clientconnSocket))
    threading.Thread(target = LetTheConnectionsBegin, args = (clientconnSocket, clientAddr)).start()