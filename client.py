"""
Fall 2022 - CSC573
Author: Subramanian Venkataraman <svenka25@ncsu.edu>
"""

#Importing necessary packages
import os
import re
import sys
import random
import threading
import signal
import fnmatch
import platform
from time import *
from socket import *
from collections import defaultdict

#RESPONSE MESSAGES
respMessages = {200:"200 OK", 400:"400 Bad Request", 404:"404 Not Found", 505:"505 P2P-CI Version Not Supported"}
p2pversion = "P2P-CI/1.0"

#Client Setup
serverListeningPort = 7734
clientAddress = socket.gethostbyname(socket.gethostname())
clientName = socket.gethostname()
serverName = "DESKTOP-IP1CNJD"
serverAddress = socket.gethostbyname(serverName)
PEER_PORT = 33001 #Hardcoded for now
P2S_SOCKET = 0
BUFFER_SIZE = 2048

RFCs_Held = [
	{'RFCNumber': 791, 'Title': 'Internet Protocol'},
	{'RFCNumber': 793, 'Title': 'Transmission Control Protocol'},
	{'RFCNumber': 1058, 'Title': 'Routing Information Protocol'},
	{'RFCNumber': 2328, 'Title': 'OSPF Version 2'}
]

# PEER_RFC_LIST = {"RFC Number": [], "RFC Title": [], "Peer Name": [], "Peer Port": []}
PEER_RFC_LIST = defaultdict(list) #Format: {RFCNumber: [Peer_HostName--PeerPort--RFC Title]}
RFC_PATH = "client_A/"

def formatDetail(itemA,itemB,itemC):
    return "{}--{}--{}".format(itemA,itemB,itemC)

def ErrorFromServer(serverReply):
    print("\n Unfortunately, there's been an error")
    if respMessages[400] in serverReply:
        print("\n Server says: {}".respMessages[400])
    elif respMessages[404] in serverReply:
        print("\n Server says: {}".respMessages[404])
    elif respMessages[505] in serverReply:
        print("\n Server says: {}".respMessages[505])
    else:
        print("\n Cannot handle this Server Error" )

def startUploadServer():
	P2P_SOCKET = socket(AF_INET, SOCK_STREAM)
    try:
        P2P_SOCKET.bind((clientName, PEER_PORT))
        P2P_SOCKET.listen()
        print("\nPeer is ready......")

        while True:
            peersocket, peeraddr = P2P_SOCKET.accept()
            threading.Thread(target = peerTransfer, args = (peersocket, peeraddr)).start()
    
    except error, (value, message):
        print("\nException: while binding the peer...")
        print("\nPeer Upload Stopped. Please try again...")
        P2P_SOCKET.close()
        del P2P_SOCKET
        exit(message)

def peerTransfer(peersocket, peeraddr):
    print("\n\n Connected to Peer {}".format(peeraddr))
    flag = 0
    incoming_data = []
    while True:
        fragment = peersocket.recv(2048)
        incoming_data.append(fragment.decode('utf-8'))
        if '\r\n\r\n' in fragment.decode('utf-8'):
            break

    incoming_request = ''.join(incoming_data)

    if 'GET' not in incoming_request:
        clientMessage = respMessages[400] + 'Closing Connection. \r\n\r\n'
        print("\n{}\n".format(clientMessage))
        peersocket.sendall(clientMessage.encode('utf-8'))
        peersocket.close()
        return 0

    p2pver = 'P2P-CI/' + re.search('P2P-CI/(.*)\r\n', incoming_request).group(1)
    rfcDetail = re.search('RFC (.*) P2P', incoming_request).group(1)
    sendFile = RFC_PATH + 'rfc' + rfcDetail + ".txt"
    date = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())

    if p2pver != p2pversion:
        flag = 0
        clientMessage = p2pver + respMessages[505] + "\r\n Date: {}\r\nOS: {}\r\n\r\n".format(date, platform.platform())
        peersocket.sendall(clientMessage.encode('utf-8'))
    
    elif not os.path.isfile(sendFile):
        flag = 0
        clientMessage = p2pver + respMessages[404] + "\r\n Date: {}\r\nOS: {}\r\n\r\n".format(date, platform.platform())
        peersocket.sendall(clientMessage.encode('utf-8'))
    
    else:
        flag = 1
        print("\n Peer is requesting RFC {}".format(rfcDetail))
        clientMessage = "{} {}\r\nDate:{}\r\nOS: {}\r\nLast-Modified: {}\r\nContent-Length: {}\r\nContent-Type: text/text\r\nData:". \
                        format(p2pver, respMessages[200], date, platform.platform(), os.path.getmtime(sendFile), os.path.getsize(sendFile))
        peersocket.sendall(clientMessage.encode('utf-8'))

        with open(sendFile, 'rb') as f:
            content = f.read(8192)
            while content:
                print("\nSending file content...")
                peersocket.sendall(data)
                content = f.read(8192)
            print("\n File Transfer Completed")
            peersocket.sendall("\r\n\r\n".encode('utf-8'))

    if flag:
        print("\n File transfer successfully completed with Peer {}. Connection closed".format(peeraddr))
    else:
        print("\n File transfer unsuccessful with Peer {}. Connection closed".format(peeraddr))
    
    peersocket.close()
    return 1

def sayHelloToServer():
    global P2S_SOCKET
    P2S_SOCKET = socket(AF_INET, SOCK_STREAM)
    print("\n Initiating Connection with Server...")
    print("\n Connecting with Server {} on {}".format(serverAddress, serverListeningPort))

    try:
        P2S_SOCKET.connect((serverAddress, serverListeningPort))
        return 1
    except error as err:
        print("\n Error {} while connecting with Server {}".format(err, serverAddress))
    except Exception as e:
        print("\n Exception {} while connecting with Server {}".format(e, serverAddress))
    
    return 0

def revealYourself():
    errorFlag = 0
    for rfc in RFCs_Held:
        clientMessage = "ADD RFC {} P2P-CI/1.0\r\nHost:{}\r\nPort:{}\r\nTitle:{}\r\n\r\n".format(rfc['RFCNumber'], clientName, PEER_PORT, rfc['Title'])
        print("\nPublishing RFC {}".format(rfc['RFCNumber']))
            
        #Send all the RFCs in your system
        incoming_data = []
        try:
            P2S_SOCKET.sendall(clientMessage.encode('utf-8'))
            while True:
                fragment = P2S_SOCKET.recv(2048)
                incoming_data.append(fragment.decode('utf-8'))
                if "\r\n\r\n" in fragment.decode('utf-8'):
                    break
        
        except error as err:
            errorFlag = 1
            print("Socket Error {} at Line: {}".format(err, sys.exc_info()[-1].tb_lineno))
            continue #Other files waiting
        
        except Exception as e:
            errorFlag = 1
            print("Socket Exception {} at Line: {}".format(e, sys.exc_info()[-1].tb_lineno))
            continue #Other files waiting

        serverResponse = ''.join(incoming_data)
        if respMessages[200] in serverResponse:
            print("\n All your RFCs were published successfully.")
        else:
            errorFlag = 1
            ErrorFromServer(serverResponse)

    if errorFlag:
        return 0
    else:
        return 1

def NowYouSeeMeToo():
    clientMessage = "LIST ALL P2P-CI/1.0\r\nHost:{}\r\nPort:{}\r\n\r\n".format(clientName, PEER_PORT)
    replyData = []

    try:
        P2S_SOCKET.sendall(clientMessage.encode('utf-8'))
        while True:
            fragment = P2S_SOCKET.recv(2048)
            replyData.append(fragment.decode('utf-8'))
            if "\r\n\r\n" in fragment.decode('utf-8'):
                break
        
    except error as err:
        print("\n Socket Error: {}".format(err))
        return 0
    
    except Exception as e:
        print("\n Socket Exception: {}".format(e))
        return 0

    
    replyDataStr = ''.join(replyData)
    if respMessages[200] in replyDataStr:
        rfcList = replyDataStr.split("\r\n\r\n")[0].split("\r\n")[1:]
        print("\n Following RFCs received:\n{}\n".format(rfcList))

        global PEER_RFC_LIST
        for rfc in rfcList:
            rfc = rfc.split()
            PEER_RFC_LIST[rfc[0]].append(formatDetail(rfc[2], rfc[3], rfc[1]))
        return 1        
    else:
        ErrorFromServer(replyDataStr)
        return 0

def sayonara():
    clientMessage = "DISCONNECT P2P-CI/1.0\r\nHost:{}\r\n\r\n".format(clientName)
    try:
        P2S_SOCKET.sendall(clientMessage.encode('utf-8'))
        P2S_SOCKET.close()
        return 1
    
    except error as err:
        print("\n Socket Error {}".format(err))
        return 0

    except Exception as e:
        print("\n Socket Exception {}".format(e))
        return 0

def PoofProgram(recv_signal, frame):
    print("\n\n Toodaloo...")
    exit()

# Handling the options at Client
if __name__ == "__main__":
    signal.signal(signal.SIGINT, PoofProgram)
    good_old_menu_options = {
        1:"Register (say hello to server)",
        2:"PUBLISH RFCs (ADD)",
        3:"LIST all RFCs at Server's CI",
        4:"LOOKUP RFCs",
        5:"Download RFC from a Peer",
        6:"Publish New RFC",
        7:"DISCONNECT yourself"
    }

    while True:
        print("\n---------------------------------------------------------------------\n")
        #Printing the Menu
        for num, option in good_old_menu_options.items():
            print("\n{}.\t {}".format(num, option))

        choice = int(input("What's on your mind today?:"))

        if choice == 1:
            if sayHelloToServer(): #Once registered to server, waiting for other Peers to cconact
                threading.Thread(target = startUploadServer, args = ()).start()
                if not revealYourself():
                    print("\n Unable to ADD all RFCs on the server. Try again later.")
            else:
                print("\n Server seems to be busy. Try again")
        
        elif choice == 2:
            if not revealYourself():
                print("\n Unable to ADD all RFCs on the server. Try again later.")
        
        elif choice == 3:
            if not NowYouSeeMeToo():
                print("\n Unable to LIST all RFCs on the server. Try again later.")
        
        elif choice == 4:
            rfcToLookup = int(input("Enter RFC Number you need to check: "))
            if not KnockKnock(rfcToLookup):
                print("\n Unable to LOOKUP requested RFC on the server. Looks like no Peer has that yet. Try again later.")
        
        elif choice == 5:
            rfcToDownload = int(input("Enter RFC Number you need to download: "))
            if not downloadRFC(rfcToDownload):
                print("\n Unable to DOWNLOAD requested RFC from peer. Try again later or with a different peer.")
        
        elif choice == 6:
            rfcToPublish = int(input("Enter RFC Number you need to publish: "))
            if not publishNewRFC(rfcToPublish):
                print("\n Unable to UPDATE requested RFC to server. Try again later.")
        
        elif choice == 7:
            if not sayonara():
                print("\n Unable to get off of Server yet. Try again later.")
            else:
                break

        else:
            print("\n Did you check the options correctly? You shouldn't be here.")

    print("\n Toodaloo")

