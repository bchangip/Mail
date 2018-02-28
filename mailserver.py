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

heloMatch = re.compile('^HELO [a-zA-Z0-9-]+(\.[a-zA-Z0-9-.]+)*$')
mailFromMatch = re.compile('(^MAIL FROM: <[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+>$)')
rcptToMatch = re.compile('(^RCPT TO: <[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+>$)')
dataMatch = re.compile('^DATA$')
quitMatch = re.compile('^QUIT$')

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


def mailRequestHandler(conn, addr):
	print("Connected by", addr)
	# data = conn.recv(1024).strip()
	
	# Connect phase
	conn.send("220 smtp.chan.com\r\n".encode())

	# HELO phase
	heloPending = True

	while heloPending:
		# expectingHELO = conn.recv(1024).strip()
		expectingHELO = receiveOneLine(conn)
		print("expectingHELO", expectingHELO)
		matched = heloMatch.match(expectingHELO)
		if matched:
			conn.send("250 smtp.chan.com, I am glad to meet you\r\n".encode())
			sourceDomain = expectingHELO.split(" ")[1].rstrip()
			heloPending = False
		else:
			conn.send("500 Syntax error\r\n".encode())

	# MAIL FROM phase
	mailFromPending = True

	while mailFromPending:
		expectingMAILFROM = receiveOneLine(conn)
		print("expectingMAILFROM", expectingMAILFROM)
		matched = mailFromMatch.match(expectingMAILFROM)
		if matched:
			conn.send("250 Ok\r\n".encode())
			mailFrom = expectingMAILFROM.split(":")[1].rstrip()
			mailFromPending = False
		else:
			conn.send("500 Syntax error\r\n".encode())


	# RCPT TO phase
	rcptToPending = True

	expectingRCPTTO = receiveOneLine(conn)

	recipients = []
	while rcptToPending:
		matched = rcptToMatch.match(expectingRCPTTO)
		if matched:
			conn.send("250 Ok\r\n".encode())
			recipients.append(expectingRCPTTO.split(":")[1][1:].rstrip()[1:-1])
			expectingRCPTTO = receiveOneLine(conn)
			if (rcptToMatch.match(expectingRCPTTO) == None):
				if (dataMatch.match(expectingRCPTTO) != None):
					expectingDATA = expectingRCPTTO
					break
		else:
			conn.send("500 Syntax error\r\n".encode())
			expectingRCPTTO = receiveOneLine(conn)


	# DATA phase
	conn.send("354 Go ahead, finish data with <CRLF>.<CRLF>\r\n".encode())

	dataBuffer = receiveMultiLine(conn)

	conn.send("250 Data completed\r\n".encode())

	# QUIT phase
	quitPending = True

	while quitPending:
		expectingQUIT = conn.recv(1024).strip()
		matched = quitMatch.match(expectingQUIT)
		if matched:
			conn.send("221 Bye\r\n".encode())
			quitPending = False
		else:
			conn.send("500 Syntax error\r\n".encode())

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
