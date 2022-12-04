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
from collections import defaultdict
import fnmatch

#RESPONSE MESSAGES
respMessages = {200:"200 OK", 400:"400 Bad Request", 404:"404 Not Found", 505:"505 P2P-CI Version Not Supported"}
p2pversion = "P2P-CI/1.0"

#Server Setup
serverListeningPort = 7734
serverAddress = gethostbyname(gethostname())
serverName = gethostname()
serverSocket = socket(AF_INET,SOCK_STREAM)
BUFFER_SIZE = 2048

try:
    serverSocket.bind((serverAddress, serverListeningPort))
    serverSocket.listen(10)
    print("\nServer is ready......")
except error as message:
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
        pattern = hostDetail+"--*"

        if methodName == "ADD":
            rfcDetail = clientHeader.split()[2]
            p2pver = clientHeader.split()[3]
            portDetail = clientData[2].split(":")[1].strip()
            rfcTitle = clientData[3].split(":")[1].strip()
            try:
                assert p2pver == p2pversion, respMessages[505]
            except AssertionError as e:
                print("\n{}".format(e))
                print("\n Client using unsupported P2P version. Connection closing")
                clientconnSocket.close()
                break         

            if rfcDetail in RFCtoClientMap.keys():
                matching = fnmatch.filter(RFCtoClientMap[rfcDetail], pattern)
                if len(matching) > 0:
                    replyMessage = "{} {}".format(p2pversion, respMessages[200]) + "\r\n\r\n"
                    print("{} \n".format(replyMessage))
                    clientconnSocket.sendall(replyMessage.encode('utf-8'))
                    continue
            
            matching = fnmatch.filter(ActiveConnList, pattern)
            if len(matching) == 0:
                ActiveConnList.append(formatConnectionDetail(hostDetail, portDetail))
            
            RFCtoClientMap[rfcDetail].append(formatConnectionDetail(hostDetail, rfcTitle))
            replyMessage = "{} {} \r\nRFC {} {} {} {}".format(p2pversion, respMessages[200], rfcDetail, rfcTitle, hostDetail, portDetail)
            print("\n{} \n".format(replyMessage))            
            clientconnSocket.sendall(replyMessage.encode('utf-8'))
            print("\n Added RFC detail from Client to CI")

        elif methodName == "LIST":
            replyMessage = p2pversion+" "+respMessages[200]+"\r\n\r\n"
            print("\n Print the whole index of RFCs from the server")
            print("\n\n Who has what you wonder?. Here you go")
            for key, value in RFCtoClientMap.items():
                # print("\n RFC Number: {} \t --- \t Clients {}".format(key, value))
                matching = fnmatch.filter(value, pattern)
                if len(matching) > 0:
                    hname = matching[0].split("--")[0]
                    hpattern = hname + "--"
                    hmatch = fnmatch.filter(ActiveConnList, hpattern)
                replyMessage += "{} {} {} {}\r\n".format(key, value.split("--")[1], value.split("--")[0], hmatch[0].split("--")[1])
            replyMessage += "\r\n"
            print("\n{} \n".format(replyMessage))
            clientconnSocket.sendall(replyMessage.encode('utf-8'))

        elif methodName == "DISCONNECT":
            print("\n Peer {} is disconnected. Connection  is closed".format(hostDetail))
            clientconnSocket.close()

            #Remove all details about the peer from CI
            #Format: "PeerName--PortNumber"
            matching = fnmatch.filter(ActiveConnList, pattern)
            ActiveConnList.remove(matching[0])

            # Format: "{RFCNumber: [Peer_Hostname--RFC Title]}"
            for k, v in RFCtoClientMap.items():
                rfcmatching = fnmatch.filter(v, pattern)
                if len(rfcmatching) > 0:
                    RFCtoClientMap[k].remove(rfcmatching[0])
                if len(RFCtoClientMap[k]) == 0:
                    del RFCtoClientMap[k]
            break

        elif methodName == "LOOKUP":
            rfcDetail = clientHeader.split()[2]
            p2pver = clientHeader.split()[3]
            try:
                assert p2pver == p2pversion, respMessages[505]
            except AssertionError as e:
                print("\n{}".format(e))
                print("\n Client using unsupported P2P version. Connection closing")
                clientconnSocket.close()
                break

            print("\n LOOKUP request received from {} for {}".format(hostDetail, rfcDetail))
            if rfcDetail not in RFCtoClientMap.keys():
                replyMessage = p2pversion+" "+respMessages[404]+"\r\n"
            else:
                replyMessage = p2pversion+" "+respMessages[200]+"\r\n"
                for i in RFCtoClientMap[rfcDetail]:
                    hname = i.split("--")[0]
                    hpattern = hname + "--"
                    hmatch = fnmatch.filter(ActiveConnList, hpattern)
                    replyMessage += "{} {} {}\r\n".format(rfcDetail, hname, hmatch[0].split("--")[1])
            replyMessage += "\r\n"
            print("\n{} \n".format(replyMessage))
            clientconnSocket.sendall(replyMessage.encode('utf-8'))
        
        else:
            #None of the provided methods - ==> Bad Request
            replyMessage = respMessages[400] + "\r\n\r\n"
            print("\n{}\n".format(replyMessage))
            clientconnSocket.sendall(replyMessage.encode('utf-8'))
            NowYouSeeMe()

def NowYouSeeMe():
    print("\n\n Active Connection List:")
    for i in range(len(ActiveConnList)):
        peer, port = i.split("-")[0], i.split("-")[1]
        print("\nPeerName:{} \t --- \t RFC Port Number:{}".format(peer, port))
    print("\n")

    print("\n\n Who has what you wonder?. Here you go")
    for key, value in RFCtoClientMap.items():
        print("\n RFC Number: {} \t --- \t Clients {}".format(key, value))
    print("\n")

# def PoofProgram(recv_signal, frame):
#     print("\n\n Toodaloo...")
#     exit()

#This is where Server keeps accepting Connections from Peers
while True:
    # signal.signal(signal.SIGINT, PoofProgram)
    clientconnSocket, clientAddr = serverSocket.accept()
    print("\n Connected to client {} with port # {}".format(clientAddr, clientconnSocket))
    threading.Thread(target = LetTheConnectionsBegin, args = (clientconnSocket, clientAddr)).start()