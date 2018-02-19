# Universidad del Valle de Guatemala
# Alejandro Cortes - 14095
# Bryan Chan - 14469
# SMTP server

import thread
import socket
import os
import re

HOST = ""
PORT = 2407

heloMatch = re.compile('^HELO \S*$')
mailFromMatch = re.compile('(^MAIL FROM: <[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+>$)')
rcptToMatch = re.compile('(^RCPT TO: <[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+>$)')
dataMatch = re.compile('^DATA$')
quitMatch = re.compile('^QUIT$')


def mailRequestHandler(conn, addr):
	print("Connected by", addr)
	# data = conn.recv(1024).strip()
	
	# Connect phase
	conn.send("220 smtp.chan.com\n".encode())

	# HELO phase
	heloPending = True

	while heloPending:
		expectingHELO = conn.recv(1024).strip()
		matched = heloMatch.match(expectingHELO)
		if matched:
			conn.send("250 smtp.chan.com, I am glad to meet you\n".encode())
			sourceDomain = expectingHELO.split(" ")[1].rstrip()
			heloPending = False
		else:
			conn.send("500 Syntax error\n".encode())

	# MAIL FROM phase
	mailFromPending = True

	while mailFromPending:
		expectingMAILFROM = conn.recv(1024).strip()
		print("expectingMAILFROM", expectingMAILFROM)
		matched = mailFromMatch.match(expectingMAILFROM)
		if matched:
			conn.send("250 Ok\n".encode())
			mailFrom = expectingMAILFROM.split(":")[1].rstrip()
			mailFromPending = False
		else:
			conn.send("500 Syntax error\n".encode())


	# RCPT TO phase
	rcptToPending = True

	expectingRCPTTO = conn.recv(1024).strip()

	recipients = []
	while rcptToPending:
		matched = rcptToMatch.match(expectingRCPTTO)
		if matched:
			conn.send("250 Ok\n".encode())
			recipients.append(expectingRCPTTO.split(":")[1][1:].rstrip()[1:-1])
			expectingRCPTTO = conn.recv(1024).strip()
			if (rcptToMatch.match(expectingRCPTTO) == None):
				if (dataMatch.match(expectingRCPTTO) != None):
					expectingDATA = expectingRCPTTO
					break
		else:
			conn.send("500 Syntax error\n".encode())
			expectingRCPTTO = conn.recv(1024).strip()


	# DATA phase
	conn.send("354 Go ahead, finish data with <CRLF>.<CRLF>\n".encode())

	currentData = ""
	dataBuffer = []
	while(currentData != "."):
		currentData = conn.recv(1024).strip()
		print("Appending",currentData)
		dataBuffer.append(currentData)

	dataBuffer = dataBuffer[:-1]

	conn.send("250 Data completed\n".encode())

	# QUIT phase
	quitPending = True

	while quitPending:
		expectingQUIT = conn.recv(1024).strip()
		matched = quitMatch.match(expectingQUIT)
		if matched:
			conn.send("221 Bye\n".encode())
			quitPending = False
		else:
			conn.send("500 Syntax error\n".encode())

	conn.close()

	content = "".join(dataBuffer)

	print("Domain: "+sourceDomain+"\nFrom: "+mailFrom+"\nTo: "+str(recipients)+"\nData: "+content)

	recipients = list(filter(lambda x: x.split('@')[1] != "uvg.mail", recipients))
	serverNames = set(map(lambda x: x.split('@')[1], recipients))
	print("serverNames", serverNames)


	for serverName in serverNames:
		serverIP = socket.gethostbyname(serverName)
		ownAccounts = list(filter(lambda x: x.split('@')[1] == serverName, recipients))
		print("serverName", serverName)
		print("serverIP", serverIP)
		print("ownAccounts", ownAccounts)

		try:
				smtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				smtpSocket.connect((serverIP, 25))
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				smtpSocket.sendall(bytes(str("HELO "+sourceDomain).encode()))
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))

				#MAIL FROM
				command = "MAIL FROM: <" + mailFrom + ">"
				# print (command)
				smtpSocket.sendall(command.encode())
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				for mail in ownAccounts:
					print (mail)
					smtpSocket.sendall(("RCPT TO: <" + mail + ">").encode())
					time.sleep(sleep_time)
					data = smtpSocket.recv(1024)
					print('Received', repr(data))
				#DATA
				smtpSocket.sendall(b'DATA')
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				# Send message.
				smtpSocket.sendall(content.encode())
				time.sleep(sleep_time)
				#. (Enviar .)
				smtpSocket.sendall(b'.')
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				#QUIT
				smtpSocket.sendall(b'QUIT')
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				smtpSocket.close() # Este close no se si va a ser necesario, porque el server cierra la conexion
		except:
			smtpSocket.close()




s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(1)
while True:
	conn, addr = s.accept()
	thread.start_new_thread(mailRequestHandler, (conn, addr))
