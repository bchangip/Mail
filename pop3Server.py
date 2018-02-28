# Universidad del Valle de Guatemala
# Alejandro Cortes - 14095
# Bryan Chan - 14469
# SMTP server

import thread
import socket
import os
import re
import time
import pprint
from pymongo import MongoClient

sleep_time = 0

dbclient = MongoClient('localhost', 27017)

HOST = ""
PORT = 2408

userMatch = re.compile('^USER \S*$')
passMatch = re.compile('^PASS \S*$')
listMatch = re.compile('^LIST$')
retrMatch = re.compile('^RETR \d*$')
deleMatch = re.compile('^DELE \d*$')
quitMatch = re.compile('^QUIT$')


# userMatch = re.compile('^user \S*$')
# passMatch = re.compile('^pass \S*$')
# listMatch = re.compile('^list$')
# retrMatch = re.compile('^retr \d*$')
# deleMatch = re.compile('^dele \d*$')
# quitMatch = re.compile('^quit$')

def receiveOneLine(conn):
	message = ""
	while "\r\n" not in message:
		message += conn.recv(1024).decode()
	return message.strip()

def receiveMultiLine(conn):
	message = ""
	while "\r\n.\r\n" not in message:
		message += conn.recv(1024).decode()
	return message.split("\r\n")[:-2]

def pop3RequestHandler(conn, addr):
	print("Connected by", addr)

	# Connect phase
	conn.send("+OK POP3 server ready\r\n".encode())

	# USER phase
	userPending = True

	while userPending:
		try:
			expectingUSER = conn.recv(1024).strip()
			user = expectingUSER.split(" ")[1].rstrip()
			matched = dbclient.mailServer.users.find_one({"user":user})
			if (matched != None):
				conn.send("OK User accepted\r\n".encode())
				# user = expectingUSER.split(" ")[1].rstrip()
				userPending = False
			else:
				conn.send("ERROR\r\n".encode())
		except:
			conn.send("-ERR\r\n".encode())


	# Pass phase
	passPending = True

	while passPending:
		try:
			expectingPASS = conn.recv(1024).strip()
			password = expectingPASS.split(" ")[1].rstrip()
			matched = dbclient.mailServer.users.find_one({"user":user})
			if (matched['password'] == password):
				conn.send("OK Pass accepted\r\n".encode())
				# password = expectingPASS.split(" ")[1].rstrip()
				passPending = False
			else:
				conn.send("ERROR\r\n".encode())
		except:
			conn.send("-ERR\r\n".encode())

	# Program phase

	while ((passPending == False) and (userPending == False)):
		expectingCommand = conn.recv(1024).strip()
		if quitMatch.match(expectingCommand):
			conn.send("+OK POP3 server signing off\r\n".encode())
			conn.close()
			break
		elif listMatch.match(expectingCommand):
			exampleIDsList = [1, 2, 3, 4, 5]
			response = "+OK " + str(len(exampleIDsList)) + " messages\r\n"
			conn.send(response.encode())
			for id in exampleIDsList:
				# time.sleep(sleep_time)
				conn.send(bytes(str(id)+"\r\n"))
			print("Finished sending ids")
			conn.send(bytes(".\r\n"))
			# Return email IDs from mongo
		elif retrMatch.match(expectingCommand):
			emailID = expectingCommand.split(" ")[1].rstrip()

			exampleResultEmail = { "MAILFROM" : "mschang@gmail.com", "RCPTTO" : "xchangip@gmail.com", "DATA" : "Hola, este es un correo de prueba" }
			response = bytes((exampleResultEmail['DATA'] + "\r\n").encode())
			conn.send(response)
			conn.send(bytes(".\r\n"))
			# Return single email from mongo
		elif deleMatch.match(expectingCommand):
			conn.send("DELETE SINGLE EMAIL\r\n".encode())
			emailID = expectingCommand.split(" ")[1].rstrip()
			# Delete single email from mongo
		else:
			conn.send("-ERR\r\n".encode())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(1)
while True:
	conn, addr = s.accept()
	thread.start_new_thread(pop3RequestHandler, (conn, addr))
