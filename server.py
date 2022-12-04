"""
Fall 2022 - CSC573
Author: Subramanian Venkataraman <svenka25@ncsu.edu>
"""

#Importing necessary packages
import time
import datetime
import threading
from _thread import *
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
serverSocket = socket(AF_INET, SOCK_STREAM)
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
ActiveConnList = {} #Format: "{PeerName:PortNumber}"
RFCtoClientMap = defaultdict(list) # Format: "{(RFCNumber, RFCTitle): [Peer_Hostname]}"

def formatConnectionDetail(hostName, portDetail):
    return "{}--{}".format(hostName, portDetail)

def LetTheConnectionsBegin(clientconnSocket):
    global ActiveConnList
    global RFCtoClientMap
    # print("First time for this thread", NowYouSeeMe())

    while True:
        clientData = clientconnSocket.recv(2048)
        clientData = clientData.decode('utf-8').split("\r\n")

        header = clientData[0]
        methodName = header.split()[0]
        hostDetail = clientData[1].split(":")[1].strip()
        # pattern = hostDetail+"--*"

        if methodName == "ADD":
            rfcDetail = int(header.split()[2])
            p2pver = header.split()[3]
            portDetail = int(clientData[2].split(":")[1])
            rfcTitle = clientData[3].split(":")[1]
            # try:
            #     assert p2pver == p2pversion, respMessages[505]
            # except AssertionError as e:
            #     print("\n{}".format(e))
            #     print("\n Client using unsupported P2P version. Connection closing")
            #     clientconnSocket.close()
            #     break         

            if (rfcDetail, rfcTitle) in RFCtoClientMap.keys():
                if hostDetail == RFCtoClientMap[(rfcDetail, rfcTitle)]:
                    replyMessage = "{} {}".format(p2pversion, respMessages[200]) + "\r\n\r\n"
                    print("{} \n".format(replyMessage))
                    clientconnSocket.sendall(replyMessage.encode('utf-8'))
                    continue
            
            if hostDetail not in ActiveConnList.keys():
                ActiveConnList[hostDetail] = portDetail
            
            RFCtoClientMap[(rfcDetail, rfcTitle)].append(hostDetail)
            replyMessage = "{} {}\r\nRFC {} {} {} {}".format(p2pversion, respMessages[200], rfcDetail, rfcTitle, hostDetail, portDetail)
            print("\nReplyMessage: \n{} \n".format(replyMessage))
            clientconnSocket.sendall(replyMessage.encode('utf-8'))
            print("\nAdded RFC detail from Client to Server's CI")
            NowYouSeeMe()

        elif methodName == "LIST":
            replyMessage = p2pversion+" "+respMessages[200]+"\r\n"
            print("\nPrint the whole index of RFCs from the server")
            print("\n\nWho has what you wonder?. Here you go")
            for k, v in RFCtoClientMap.items():
                replyMessage += "{} {} {} {}\r\n".format(k[0],v, ActiveConnList[v], k[1])
            replyMessage += "\r\n"
            print("\nReplyMessage: \n{} \n".format(replyMessage))
            clientconnSocket.sendall(replyMessage.encode('utf-8'))

        elif methodName == "DISCONNECT":
            print("\nPeer {} is disconnected. Connection is closed".format(hostDetail))
            clientconnSocket.close()

            #Remove all details about the closed peer from CI
            #Format: "{PeerName:PortNumber}"
            if hostDetail in ActiveConnList.keys():
                del ActiveConnList[hostDetail]

                #Format: "{(RFCNumber, RFCTitle): [Peer_Hostname]}"
                for k, v in RFCtoClientMap.items():
                    if v == hostDetail:
                        RFCtoClientMap[k].remove(hostDetail)

                    if len(RFCtoClientMap[k]) == 0:
                        del RFCtoClientMap[k]
                NowYouSeeMe()
            break

        elif methodName == "LOOKUP":
            rfcDetail = header.split()[2]
            p2pver = header.split()[3]
            portDetail = int(clientData[2].split(":")[1].strip())
            rfcTitle = clientData[3].split(":")[1].strip()
            # try:
            #     assert p2pver == p2pversion, respMessages[505]
            # except AssertionError as e:
            #     print("\n{}".format(e))
            #     print("\n Client using unsupported P2P version. Connection closing")
            #     clientconnSocket.close()
            #     break

            print("\n LOOKUP request received from {} for {}".format(hostDetail, rfcDetail))
            if (rfcDetail, rfcTitle) not in RFCtoClientMap.keys():
                replyMessage = p2pversion+" "+respMessages[404]+"\r\n\r\n"
            else:
                replyMessage = p2pversion+" "+respMessages[200]+"\r\n"
                for k, v in RFCtoClientMap.items():
                    if rfcDetail == k[0]:
                        replyMessage += "RFC {} {} {} {} \r\n".format(rfcDetail, k[1], v, ActiveConnList[v])
                print("\nReplyMessage: \n{} \n".format(replyMessage))
                replyMessage += "\r\n"
            
            clientconnSocket.sendall(replyMessage.encode('utf-8'))
        
        else:
            #None of the provided methods - ==> Bad Request
            replyMessage = respMessages[400] + "\r\n\r\n"
            print("\nReplyMessage: \n{} \n".format(replyMessage))
            clientconnSocket.sendall(replyMessage.encode('utf-8'))

def NowYouSeeMe():
    print("\n\nActive Connection List:")
    for k, v in ActiveConnList.items():
        print("\nPeerName:{} \t --- \t RFC Port Number:{}".format(k, v))
    print("\n")

    print("\n\nWho has what you wonder?. Here you go")
    for key, value in RFCtoClientMap.items():
        print("\nRFC Number: {} \t --- \t RFC Title {} \t --- \t Clients {}".format(key[0], key[1], value))
    print("\n")

def PoofProgram(recv_signal, frame):
    print("\n\nToodaloo...")
    exit()

#This is where Server keeps accepting Connections from Peers
signal.signal(signal.SIGINT, PoofProgram)
while True:
    clientconnSocket, clientAddr = serverSocket.accept()
    print("\n Connected to client {}".format(clientAddr))
    # threading.Thread(target = LetTheConnectionsBegin, args = (clientconnSocket, clientAddr)).start()
    start_new_thread(LetTheConnectionsBegin, (clientconnSocket, ))