"""
Fall 2022 - CSC573
Author: Subramanian Venkataraman <svenka25@ncsu.edu>
"""
#Importing necessary packages
from socket import *
from _thread import *
from signal import signal, SIGINT
from collections import defaultdict
from more_itertools import locate

#RESPONSE MESSAGES
respMessages = {200:"200 OK", 400:"400 Bad Request", 404:"404 Not Found", 505:"505 P2P-CI Version Not Supported"}
p2pversion = "P2P-CI/1.0"

#Server Setup
serverListeningPort = 7734
serverAddress = '127.0.0.1'
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverAddress, serverListeningPort))
serverSocket.listen(10)

#Initial Lists maintained by server
ActiveConnList = {} #Format: "{PeerName:PortNumber}"
RFCtoClientMap = {"RFC_#": [], "RFC_Title": [], "Peer_HostName": []}

print("\nServer is ready......")

def formatConnectionDetail(hostName, portDetail):
    return "{}--{}".format(hostName, portDetail)

def LetTheConnectionsBegin(clientconnSocket):
    global ActiveConnList
    global RFCtoClientMap

    while True:
        clientData = clientconnSocket.recv(2048)
        clientData = clientData.decode().split("\r\n")
        
        # print("\nReceived data", clientData)

        header = clientData[0].split()
        hostDetail = clientData[1].split(":")[1]
        methodName = header[0]

        if methodName == "DISCONNECT":
            print("\nClient %s disconnected. Closing connection." % hostDetail)
            clientconnSocket.close()

            if hostDetail in ActiveConnList.keys():
                del ActiveConnList[hostDetail]

                count = RFCtoClientMap["Peer_HostName"].count(hostDetail)
                for i in range(count):
                    index = RFCtoClientMap["Peer_HostName"].index(hostDetail)
                    RFCtoClientMap["Peer_HostName"].pop(index)
                    RFCtoClientMap["RFC_#"].pop(index)
                    RFCtoClientMap["RFC_Title"].pop(index)
            
            display_connList()
            break

        elif methodName == "ADD":
            alreadyPresent = 0
            print("\ndebugging ADD at server---\n", header)
            rfcDetail = header[2]
            p2pver = header[3]
            portDetail = clientData[2].split(":")[1]
            title = clientData[3].split(":")[1]

            rfcIndices = list(locate(RFCtoClientMap["RFC_#"], lambda x: x == rfcDetail))
            hostIndices = list(locate(RFCtoClientMap["Peer_HostName"], lambda x: x== hostDetail))
            titleIndices = list(locate(RFCtoClientMap["RFC_Title"], lambda x: x== title))

            commonIndices = list(set(rfcIndices).intersection(hostIndices).intersection(titleIndices))

            # print("\ndebug -- {} \n{} \n{}".format(rfcIndices, hostIndices, commonIndices))

            for idx in commonIndices:
                # print("\n {} -- {} -- {}".format(RFCtoClientMap["RFC_#"][idx], RFCtoClientMap["Peer_HostName"][idx], RFCtoClientMap["RFC_Title"][idx]))
                if RFCtoClientMap["RFC_#"][idx] == rfcDetail and RFCtoClientMap["Peer_HostName"][idx] == hostDetail and RFCtoClientMap["RFC_Title"][idx] == title:
                    alreadyPresent = 1
                    replyMessage = "{} {}\r\n\r\n".format(p2pver,respMessages[200])
                    clientconnSocket.sendall(replyMessage.encode())
                    
            if alreadyPresent == 0:
                if hostDetail not in ActiveConnList.keys():
                    ActiveConnList[hostDetail] = portDetail
                
                RFCtoClientMap["RFC_#"].append(rfcDetail)
                RFCtoClientMap["RFC_Title"].append(title)
                RFCtoClientMap["Peer_HostName"].append(hostDetail)

                replyMessage = "{} {}\r\nRFC {} {} {} {}\r\n\r\n".format(p2pver, respMessages[200], rfcDetail, title, hostDetail, portDetail)
                clientconnSocket.sendall(replyMessage.encode())

                print("\nReceived RFC from client and updated Server's CI")
            display_connList()
            
        elif methodName == "LIST":
            p2pver = header[2]
            print("\nLIST all RFCs in Server's CI")
            replyMessage = "{} {}\r\n".format(p2pver, respMessages[200])
            for i, rfc in enumerate(RFCtoClientMap["RFC_#"]):
                replyMessage += "{} {} {} {}\r\n".format(rfc, RFCtoClientMap["RFC_Title"][i], RFCtoClientMap["Peer_HostName"][i], ActiveConnList[RFCtoClientMap["Peer_HostName"][i]])
            replyMessage += "\r\n"
            clientconnSocket.sendall(replyMessage.encode())

        elif methodName == "LOOKUP":
            rfcDetail = header[2]
            p2pver = header[3]
            print("\nLOOKUP request received from {} for RFC {}".format(hostDetail, rfcDetail))
            if rfcDetail not in RFCtoClientMap["RFC_#"]:
                replyMessage = "{} {}\r\n\r\n".format(p2pver, respMessages[404])
            else:
                replyMessage = "{} {}\r\n".format(p2pver, respMessages[200])
                for i, rfc in enumerate(RFCtoClientMap["RFC_#"]):
                    if rfcDetail == rfc:
                        replyMessage += "RFC {} {} {} {}\r\n".format(rfcDetail, RFCtoClientMap["RFC_Title"][i], RFCtoClientMap["Peer_HostName"][i], ActiveConnList[RFCtoClientMap["Peer_HostName"][i]])
                    print(replyMessage)
                replyMessage += "\r\n"
            clientconnSocket.sendall(replyMessage.encode())
        else:
            print("\n400 Bad Request")
            replyMessage = "{}\r\n\r\n".format(respMessages[400])
            clientconnSocket.sendall(replyMessage.encode())

def handler(signal_received, frame):
    print('\n\nBye!')
    exit()

def display_connList():
    print("\nActive Connections List:")
    for k, v in ActiveConnList.items():
        print("\n{} - {}".format(k,v))
    
    print("\nRFC Client Mapping List:")
    print("\n RFC Number -- RFC Title -- Peer HostName")
    for i in range(len(RFCtoClientMap["RFC_#"])):
        print("\n {} -- {} -- {}".format(RFCtoClientMap["RFC_#"][i], RFCtoClientMap["RFC_Title"][i], RFCtoClientMap["Peer_HostName"][i]))

signal(SIGINT, handler)
while 1:
    clientconnSocket, addr = serverSocket.accept()
    print('\nConnected with client: ', addr)
    start_new_thread(LetTheConnectionsBegin, (clientconnSocket, ))