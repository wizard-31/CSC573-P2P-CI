"""
Fall 2022 - CSC573
Author: Subramanian Venkataraman <svenka25@ncsu.edu>
"""

#Importing necessary packages
import os
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
P2S_PORT = 0

RFCs_Held = [
	{'rfc_no': 791, 'title': 'Internet Protocol'},
	{'rfc_no': 793, 'title': 'Transmission Control Protocol'},
	{'rfc_no': 1058, 'title': 'Routing Information Protocol'},
	{'rfc_no': 2328, 'title': 'OSPF Version 2'}
]

PEER_RFCs = {"RFC Number": [], "RFC Title": [], "Peer Name": [], "Peer Port": []}
RFC_PATH = "client_A/"

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


