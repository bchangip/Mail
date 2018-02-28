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
PORT = 110

userMatch = re.compile('^USER \S*$')
passMatch = re.compile('^PASS \S*$')
statMatch = re.compile('^STAT$')
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
	print("oneliner", message)
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
		expectingUSER = receiveOneLine(conn)
		if userMatch.match(expectingUSER):
			user = expectingUSER.split(" ")[1].rstrip()
			conn.send("+OK User accepted\r\n".encode())
			userPending = False
		else:
			conn.send(bytes("-ERR\r\n".encode()))

	# Pass phase
	passPending = True

	while passPending:
		expectingPASS = receiveOneLine(conn)
		# print("expectingPASS", expectingPASS)
		if passMatch.match(expectingPASS):
			# print("Correct")
			conn.send(bytes("+OK Pass accepted\r\n".encode()))
			passPending = False
			# password = expectingPASS.split(" ")[1].rstrip()
			# matched = dbclient.mailServer.users.find_one({"user":user})
			# if (matched['password'] == password):
			# 	conn.send("+OK Pass accepted\r\n".encode())
			# 	# password = expectingPASS.split(" ")[1].rstrip()
			# 	passPending = False
			# else:
			# 	conn.send(bytes("-ERR\r\n".encode()))
		else:
			conn.send(bytes("-ERR\r\n".encode()))

	# Program phase

	while ((passPending == False) and (userPending == False)):
		expectingCommand = receiveOneLine(conn)
		if quitMatch.match(expectingCommand):
			conn.send("+OK POP3 server signing off\r\n".encode())
			conn.close()
			break
		elif statMatch.match(expectingCommand):
			# print("STAT on user", user)
			mailbox = dbclient.mailServer.emails.find({"RCPTTO": user})
			emailCount = mailbox.count()
			mailboxSize = sum(map(lambda x: len(x["DATA"]), mailbox))

			conn.send(bytes("+OK "+str(emailCount)+" "+str(mailboxSize)+"\r\n".encode()))
		elif listMatch.match(expectingCommand):
			# print("ON LIST")
			mailbox = list(dbclient.mailServer.emails.find({"RCPTTO": user}))
			emailCount = len(mailbox)
			mailboxSize = sum(map(lambda x: len(x["DATA"]), mailbox))
			response = "+OK " + str(emailCount) + " messages ("+str(mailboxSize)+" octets)\r\n"
			currentList = {}
			for mail in list(enumerate(mailbox)):
				currentList[str(int(mail[0])+1)] = mail[1]
			currentListIDs = list(currentList.keys())
			conn.send(response.encode())
			# print("currentList", currentList)
			# print("currentListIDs", currentListIDs)
			for id in currentListIDs:
				# print("id in currentListIDs", id)
				conn.send(bytes(str(id)+" "+str(len(currentList[id]["DATA"]))+"\r\n"))
			# print("Finished sending ids")
			conn.send(bytes(".\r\n"))
		elif retrMatch.match(expectingCommand):
			emailID = expectingCommand.split(" ")[1].rstrip()
			# print("currentList on retr", currentList)
			if emailID in currentList:
				# print("Retrieving id", emailID)
				conn.send(bytes("+OK "+str(len(currentList[emailID]["DATA"]))+" octets\r\n"))
				# conn.send(bytes("HOLA\r\n".encode()))
				conn.send(bytes((currentList[emailID]["DATA"]+"\r\n").encode()))
				conn.send(bytes(".\r\n"))
				# Return single email from mongo
			else:
				conn.send(bytes("-ERR no such message\r\n"))
		elif deleMatch.match(expectingCommand):
			emailID = expectingCommand.split(" ")[1].rstrip()

			if emailID in currentList:
				dbclient.mailServer.emails.remove(currentList[emailID]["_id"])
				del currentList[emailID]
				conn.send("+OK message "+str(emailID)+" deleted\r\n".encode())
			else:
				conn.send(bytes("-ERR no such message\r\n"))
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
