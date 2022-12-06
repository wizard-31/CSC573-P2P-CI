"""
Fall 2022 - CSC573
Author: Subramanian Venkataraman <svenka25@ncsu.edu>
"""
#Importing necessary packages
from socket import *
from _thread import *
from time import gmtime, strftime
from signal import signal, SIGINT
from tabulate import tabulate
import time
import pandas as pd
import re
import platform
import os
import sys
import random

#RESPONSE MESSAGES
respMessages = {200:"200 OK", 400:"400 Bad Request", 404:"404 Not Found", 505:"505 P2P-CI Version Not Supported"}
p2pversion = "P2P-CI/1.0"

HOSTNAME = "client2.csc.ncsu.edu"
SERVER_IP = 'localhost'
SERVER_PORT = 7734
PEER_PORT = 33002
P2S_SOCKET = 0

RFCs = [
	{'rfc_no': 793, 'title': 'Transmission Control Protocol'},
	{'rfc_no': 4271, 'title': 'A Border Gateway Protocol 4'}
]
PEER_RFCs = {"RFC Number": [], "RFC Title": [], "Peer Name": [], "Peer Port": []}
RFC_PATH = 'client_B/'

def startFileUpload():
	P2P_SOCKET = socket(AF_INET, SOCK_STREAM)
	P2P_SOCKET.bind(('localhost', PEER_PORT))
	print("\nPeer server started at %s and port %s\n" % (HOSTNAME, PEER_PORT))
	P2P_SOCKET.listen()

	while True:
		peer_socket, peer_addr = P2P_SOCKET.accept()
		start_new_thread(peerTransfer, (peer_socket, peer_addr, ))

def peerTransfer(peer_socket, peer_addr):
	print("\nConnected to peer ", peer_addr)
	
	transferData = []
	while True:
		fragment = peer_socket.recv(1024)
		transferData.append(fragment.decode())
		if "\r\n\r\n" in fragment.decode():
			break
	peer_request = ''.join(transferData)

	if not "GET" in peer_request:
		peerMessage = "{} . Closing Connection".format(respMessages[400])
		peer_socket.sendall(peerMessage.encode())
		peer_socket.close()
		return 0

	version = "P2P-CI/" + re.search("P2P-CI/(.*)\r\n", peer_request).group(1)
	rfcDetail = re.search("RFC (.*) P2P", peer_request).group(1)
	file = RFC_PATH + "rfc" + rfcDetail + ".txt"
	date = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.gmtime())
	
	if version != p2pversion:
		peerMessage = "{} {}\r\nDate:{}\r\nOS:{}\r\n".format(version, respMessages[505], date, platform.platform())
		data = "\r\n"
		response = peerMessage + data
		peer_socket.sendall(response.encode())

	elif not os.path.isfile(file):
		peerMessage = "{} {}\r\nDate:{}\r\nOS:{}\r\n".format(version, respMessages[404], date, platform.platform())
		data = "\r\n"
		response = peerMessage + data
		peer_socket.sendall(response.encode())

	else:
		print("\nPeer is requesting RFC ", rfcDetail)
		peerMessage = "{} {}\r\nDate:{}\r\nOS:{}\r\nLast-Modified:{}\r\nContent-Length:{}\r\nContent-Type: text/text\r\n RFC Data: ".format(version, respMessages[200], date, platform.platform(), os.path.getmtime(file), os.path.getsize(file))
		peer_socket.sendall(peerMessage.encode())

		with open(file, 'rb') as f:
			data = f.read(8192)
			while data:
				print("\nSending...")
				peer_socket.sendall(data)
				data = f.read(8192)
			print("\nFile Sent successfully!")
			peer_socket.sendall("\r\n\r\n".encode())

	print("\nConnection closed with Peer {}".format(peer_addr))
	peer_socket.close()
	return 1	

def register():
	global P2S_SOCKET
	P2S_SOCKET = socket(AF_INET, SOCK_STREAM)
	print("\nConnecting to Server {} via port {}".format(SERVER_IP, SERVER_PORT))
	try:
		P2S_SOCKET.connect((SERVER_IP, SERVER_PORT))
		return 1
	except error as e:
		print("\nServer Socket error: ", e)
	except Exception as e:
		print("\nException: ", e)

	return 0

def publish_all():
	errFlag = 0
	for rfc in RFCs:
		peerMessage = "ADD RFC {} P2P-CI/1.0\r\nHost:{}\r\nPort:{}\r\nTitle:{}\r\n\r\n".format(rfc['rfc_no'], HOSTNAME, PEER_PORT, rfc['title'])
		print("Publishing RFC: ", rfc['rfc_no'])
		# print("Debugging ADD --- \n", peerMessage)

		outgoingData = []
		try:
			P2S_SOCKET.sendall(peerMessage.encode())
			while True:
				fragment = P2S_SOCKET.recv(1024)
				outgoingData.append(fragment.decode())
				if "\r\n\r\n" in fragment.decode():
					break
		except error as e:
			errFlag = 1
			print("\nSocket error {} at Line: {}".format(sys.exc_info()[-1].tb_lineno, e))
			continue
		except Exception as e:
			errFlag = 1
			print("\nException {} at Line: {}".format(sys.exc_info()[-1].tb_lineno, e))
			continue

		server_response = ''.join(outgoingData)
		if respMessages[200] in server_response:
			print("Published Successfully! Server Response:\n {}".format(server_response))
		else:
			errFlag = 1
			handleError(server_response)

	if errFlag:
		return 0
	return 1

def lookup_rfc(rfc_no):
	peerMessage = "LOOKUP RFC {} P2P-CI/1.0\r\nHost:{}\r\n\r\n".format(rfc_no, HOSTNAME)

	outgoingData = []
	try:
		P2S_SOCKET.sendall(peerMessage.encode())
		while True:
			fragment = P2S_SOCKET.recv(1024)
			outgoingData.append(fragment.decode())
			if "\r\n\r\n" in fragment.decode():
				break

	except error as e:
		print("\nSocket error: {}".format(e))
		return 0
	except Exception as e:
		print("\nException: {}".format(e))
		return 0

	server_response = ''.join(outgoingData)
	if respMessages[200] in server_response:
		rfcs = server_response.split("\r\n")
		rfcs = rfcs[1:len(rfcs)-2]
		print("\nReceived the following RFC details from the server:\n {}".format(rfcs))

		global PEER_RFCs
		New_RFC = {"RFC Number": [], "RFC Title": [], "Peer Name": [], "Peer Port": []}
		for rfc in rfcs:
			rfc = rfc.split()
			if rfc[1] in PEER_RFCs["RFC Number"]:
				index = PEER_RFCs["RFC Number"].index(rfc[1])
				if rfc[-2] != PEER_RFCs["Peer Name"][index]:
					PEER_RFCs["RFC Number"].append(rfc[1])
					PEER_RFCs["RFC Title"].append(' '.join(rfc[2:len(rfc)-2]))
					PEER_RFCs["Peer Name"].append(rfc[-2])
					PEER_RFCs["Peer Port"].append(rfc[-1])					
			else:
				PEER_RFCs["RFC Number"].append(rfc[1])
				PEER_RFCs["RFC Title"].append(' '.join(rfc[2:len(rfc)-2]))
				PEER_RFCs["Peer Name"].append(rfc[-2])
				PEER_RFCs["Peer Port"].append(rfc[-1])
			# New_RFC["RFC Number"].append(rfc[1])
			# New_RFC["RFC Title"].append(' '.join(rfc[2:len(rfc)-2]))
			# New_RFC["Peer Name"].append(rfc[-2])
			# New_RFC["Peer Port"].append(rfc[-1])

		# print(tabulate(New_RFC, headers='keys', tablefmt='fancy_grid', showindex=True))
		return 1
	else:
		handleError(server_response)
		return 0

def list_all_rfcs():
	peerMessage = "LIST ALL P2P-CI/1.0\r\nHost:{}\r\n\r\n".format(HOSTNAME)
	outgoingData = []
	# print("Checking...3. {}".format(peerMessage))
	try:
		P2S_SOCKET.sendall(peerMessage.encode())
		while True:
			fragment = P2S_SOCKET.recv(1024)
			outgoingData.append(fragment.decode())
			if "\r\n\r\n" in fragment.decode():
				break

	except error as e:
		print("\nSocket error: {}".format(e))
		return 0
	except Exception as e:
		print("\nException: {}".format(e))
		return 0

	server_response = ''.join(outgoingData)
	if respMessages[200] in server_response:
		rfcs = server_response.split("\r\n\r\n")[0].split("\r\n")[1:]
		print("\nReceived the following RFC details from the server:\n{}\n".format(rfcs))
		
		global PEER_RFCs
		PEER_RFCs = {"RFC Number": [], "RFC Title": [], "Peer Name": [], "Peer Port": []}
		for rfc in rfcs:
			rfc = rfc.split()
			PEER_RFCs["RFC Number"].append(rfc[0])
			PEER_RFCs["RFC Title"].append(' '.join(rfc[1:len(rfc)-2]))
			PEER_RFCs["Peer Name"].append(rfc[-2])
			PEER_RFCs["Peer Port"].append(rfc[-1])

		display_RFCList()
		return 1
	else:
		handleError(server_response)
		return 0

def disconnect():
	peerMessage = "DISCONNECT P2P-CI/1.0\r\nHost:{}\r\n\r\n".format(HOSTNAME)
	try:
		P2S_SOCKET.sendall(peerMessage.encode())
		P2S_SOCKET.close()
	except error as e:
		print("\nSocket error: {}".format(e))
		return 0
	except Exception as e:
		print("\nException:{}".format(e))
		return 0
	return 1

def download_rfc(rfc_no):
	if rfc_no not in PEER_RFCs["RFC Number"]:
		print("Invalid RFC number. Available RFCs are:\n {}".format(PEER_RFCs["RFC Number"]))
		return 0

	indices = [i for i, rfc in enumerate(PEER_RFCs["RFC Number"]) if rfc == rfc_no]
	# index = random.choice(indices)
	index = indices[0]

	peer_socket = ("localhost", int(PEER_RFCs["Peer Port"][index]))
	psock = socket(AF_INET, SOCK_STREAM)
	print("\nConnecting to peer: {}".format(peer_socket))

	try:
		psock.connect(peer_socket)
	except error as e:
		print("\nPeer Socket error: {}".format(e))
		return 0
	except Exception as e:
		print("\nException: {}".format(e))
		return 0

	peerMessage = "GET RFC {} P2P-CI/1.0\r\nHost:{}\r\n\r\n".format(rfc_no, PEER_RFCs["Peer Name"][index])

	try:
		psock.sendall(peerMessage.encode())
		while True:
			fragment = psock.recv(1024).decode()
			if respMessages[200] not in fragment:
				print("\nPeer Error: {}".format(fragment))
				return 0
			if "RFC Data: " in fragment:
				data = fragment.split("RFC Data: ")[1]
				break
		
		file = RFC_PATH + "rfc" + rfc_no + ".txt"
		with open(file, 'w') as f:
			f.write(data)
			while True:
				print("Receiving...")
				data = psock.recv(8192).decode()
				if "\r\n\r\n" in data:
					data = data.split("\r\n\r\n")[0]
					f.write(data)
					break
				f.write(data)
			print("File Received! Saved Location: {}".format(file))

	except error as e:
		print("\nSocket error: {}".format(e))
		return 0
	except Exception as e:
		print("\nException: {}".format(e))
		return 0

	global RFCs
	updatedFlag = 1
	for rfc in RFCs:
		if rfc_no == rfc['rfc_no']:
			updatedFlag = 0
			break
	if updatedFlag:
		RFCs.append({'rfc_no': rfc_no, 'title': PEER_RFCs["RFC Title"][index]})
	return 1

def handleError(server_response):
	if respMessages[400] in server_response:
		print("\nServer Error: ", respMessages[400])
	elif respMessages[404] in server_response:
		print("\nServer Error: ", respMessages[404])
	elif respMessages[505] in server_response:
		print("\nServer Error: ", respMessages[505])
	else:
		print("\nServer Error: Unknown")

def display_RFCList():
	print("\nRFCs with Peers:")
	print("\nRFC_Number RFC_Title Peer_HostName Peer_port")
	for i in range(len(PEER_RFCs["RFC Number"])):
		print("\n {} -- {} -- {} -- {}".format(PEER_RFCs["RFC Number"][i], PEER_RFCs["RFC Title"][i], PEER_RFCs["Peer Name"][i], PEER_RFCs["Peer Port"][i]))

	print("####################################################")

	print("\nRFCs in local system:")
	print("\nRFC_Number RFC_Title")
	if len(RFCs):
		for i in RFCs:
			print("\n{} -- {}".format(i['rfc_no'], i['title']))        
	else:
		print("\nNo RFCs in your local system.")

def handler(signal_received, frame):
	print('\n\nBye!')
	exit()

if __name__ == '__main__':
	signal(SIGINT, handler)

	good_old_options = {
		'1': 'Register to the System',
		'2': 'Publish existing RFCs',
		'3': 'List all RFCs at the Server',
		'4': 'Lookup a RFC',
		'5': 'Download RFC from Peer',
		'6': 'Disconnect from the System'
	}

	while True: 
		print("########################################")
		for entry in good_old_options: 
			print("{}--{}".format(entry, good_old_options[entry]))

		selection = int(input("\nWhat's on your mind today?\n> "))
		if selection == 1:
			if register():
				start_new_thread(startFileUpload, ())
				if not publish_all():
					print("\nUnable to publish all available RFCs on the server. Try again later.")
			else:
				print("\nUnable to connect to server. Try again later.")
			
		elif selection == 2: 
			if not publish_all():
				print("\nUnable to publish all available RFCs on the server. Try again later.")
		
		elif selection == 3:
			if not list_all_rfcs():
				print("\nUnable to list all RFCs available on the server. Try again later.")

		elif selection == 4:
			num = input("\nEnter RFC Number to look up at server: ")
			if not lookup_rfc(num):
				print("\nOops. RFC not hosted at any peer. Try again later.")

		elif selection == 5:
			num = input("\nEnter RFC Number to download: ")
			if not download_rfc(num):
				print("\nUnable to download new RFC from peer. Try again later.")
			
		elif selection == 6:
			if not disconnect():
				print("\nUnable to disconnect from the system. Try again later.")
			else:
				break
		else:
			print("\nDid you read the options? You shouldn't be here. Try again later.")

	print("\nToodaloo.")