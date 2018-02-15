# Universidad del Valle de Guatemala
# Alejandro Cortes - 14095
# Bryan Chan - 14469
# SMTP server

import thread
import socket
import os
import re
import time

sleep_time = 0.3


HOST = ""
PORT = 2408

userMatch = re.compile('^USER \S*$')
passMatch = re.compile('^PASS \S*$')
listMatch = re.compile('^LIST$')
retrMatch = re.compile('^RETR \d*$')
deleMatch = re.compile('^DELE \d*$')
quitMatch = re.compile('^QUIT$')


def pop3RequestHandler(conn, addr):
	print("Connected by", addr)
	
	# Connect phase
	conn.send("OK POP3 server ready\n".encode())

	# USER phase
	userPending = True

	while userPending:
		expectingUSER = conn.recv(1024).strip()
		matched = userMatch.match(expectingUSER)
		if matched:
			conn.send("OK User accepted\n".encode())
			user = expectingUSER.split(" ")[1].rstrip()
			userPending = False
		else:
			conn.send("ERROR\n".encode())


	# Pass phase
	passPending = True

	while passPending:
		expectingPASS = conn.recv(1024).strip()
		matched = passMatch.match(expectingPASS)
		if matched:
			conn.send("OK Pass accepted\n".encode())
			password = expectingPASS.split(" ")[1].rstrip()
			passPending = False
		else:
			conn.send("ERROR\n".encode())

	# Program phase

	while True:
		expectingCommand = conn.recv(1024).strip()
		if quitMatch.match(expectingCommand):
			conn.send("OK POP3 server signing off\n".encode())
			conn.close()
			break
		elif listMatch.match(expectingCommand):
			exampleIDsList = [1, 2, 3, 4, 5]
			response = "OK " + str(len(exampleIDsList)) + " messages"
			conn.send(response.encode())
			for id in exampleIDsList:
				time.sleep(sleep_time)
				conn.send(bytes(str(id)))
			print("Finished sending ids")
			conn.send(b'.')
			# Return email IDs from mongo
		elif retrMatch.match(expectingCommand):
			emailID = expectingCommand.split(" ")[1].rstrip()

			exampleResultEmail = { "MAILFROM" : "mschang@gmail.com", "RCPTTO" : "xchangip@gmail.com", "DATA" : "Hola, este es un correo de prueba" }
			response = bytes(exampleResultEmail['DATA'].encode())
			conn.send(response)
			conn.send(b'.')
			# Return single email from mongo
		elif deleMatch.match(expectingCommand):
			conn.send("DELETE SINGLE EMAIL\n".encode())
			emailID = expectingCommand.split(" ")[1].rstrip()
			# Delete single email from mongo
		else:
			conn.send("ERROR\n".encode())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(1)
while True:
	conn, addr = s.accept()
	thread.start_new_thread(pop3RequestHandler, (conn, addr))