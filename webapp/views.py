# -*- coding: utf-8 -*-
# universidad del Valle de Guatemala
from __future__ import division
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
import registration.signals
from .models import EmailForm, UserForm
from django.forms import modelformset_factory
import socket
from pymongo import MongoClient

dbclient = MongoClient('localhost', 27017)

DOMAIN = "uvg.mail"
# DOMAIN = "grupo2.com"

SMTPHOST = "localhost"
# SMTPHOST = "192.168.43.17"
SMTPPORT = 25
# SMTPPORT = 2407


POP3HOST = SMTPHOST
POP3PORT = 110
# POP3PORT = 2000

loggedEmail = ""
loggedPassword = ""

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

def parseData(data):
	if "\n\n" in data:
		parsed = {}
		header, content = data.split("\n\n")
		parsed["Content"] = content

		headerInfo = header.split("\n")
		headerInfo = map(
			lambda x: x.split(": ") if ": " in x else ["Unknown", x],
			headerInfo
		)
		for headerSingleInfo in headerInfo:
			parsed[headerSingleInfo[0]] = headerSingleInfo[1]
		return parsed


	else:
		return {
			"Content": data,
			"Subject": "--Header malformed",
			"Date": "--Header malformed",
			"From": "--Header malformed",
			"To": "--Header malformed"
		}

def inboxPage(request):
	global loggedEmail
	global loggedPassword
	if loggedEmail == "":
		return redirect("loginPage")

	# Aqui deberia ir el codigo de POP3, los correos que vengan del server guardarlos en mongo
	pop3Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	pop3Socket.connect((POP3HOST, POP3PORT))
	data = receiveOneLine(pop3Socket)
	print('Received', repr(data))
	pop3Socket.sendall(bytes(str("USER "+loggedEmail+"\r\n").encode()))
	data = receiveOneLine(pop3Socket)
	print('Received', repr(data))
	pop3Socket.sendall(bytes(str("PASS "+loggedPassword+"\r\n").encode()))
	data = receiveOneLine(pop3Socket)
	print('Received', repr(data))
	pop3Socket.sendall(bytes("LIST\r\n".encode()))
	mailIndices = receiveMultiLine(pop3Socket)[1:]
	print("mailIndices", mailIndices)
	for index in mailIndices:
		index = index.split(" ")[0]
		pop3Socket.sendall(bytes(("RETR "+str(index)+"\r\n").encode()))
		mailContent = receiveMultiLine(pop3Socket)
		print("mailContent", mailContent)
		#Save message to local mongo
		dbclient.mailClient.emails.insert({"RCPTTO": loggedEmail, "DATA": mailContent[1]})
		pop3Socket.sendall(bytes(("DELE "+str(index)+"\r\n").encode()))
		receiveOneLine(pop3Socket)

	pop3Socket.sendall(bytes("QUIT\r\n".encode()))

	localEmails = list(map(
		lambda x: parseData(x["DATA"]),
		dbclient.mailClient.emails.find({"RCPTTO": loggedEmail})))

	print("localEmails", localEmails)

	return render(
		request,
		'webapp/inbox.html',
		{
			'localEmails': localEmails
		}
	)



def createEmailPage(request):
	global loggedEmail
	if loggedEmail == "":
		return loginPage
	if(request.method == 'GET'):
		return render(
			request, 
			'webapp/createEmail.html',
			{
				'createEmailForm': EmailForm()
			}
		)
	else:
		# try:
		newEmail = EmailForm(request.POST)
		if newEmail.is_valid():
			print(newEmail.cleaned_data['toEmail'])
			print(newEmail.cleaned_data['subject'])
			print(newEmail.cleaned_data['data'])

			smtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			smtpSocket.connect((SMTPHOST, SMTPPORT))
			data = receiveOneLine(smtpSocket)
			print('Received', repr(data))
			smtpSocket.sendall(bytes("HELO uvg.mail\r\n".encode()))
			# time.sleep(sleep_time)
			data = receiveOneLine(smtpSocket)
			print('Received', repr(data))

			#MAIL FROM
			command = "MAIL FROM:<" + loggedEmail + "@" + DOMAIN + ">\r\n"
			print("mailFrom", command)
			smtpSocket.sendall(bytes(command.encode()))
			# time.sleep(sleep_time)
			data = receiveOneLine(smtpSocket)
			print('Received', repr(data))
			#RCPT TO
			# print (newEmail.cleaned_data['toEmail'].split(','))
			for mail in newEmail.cleaned_data['toEmail'].split(','):
				print (mail)
				smtpSocket.sendall(("RCPT TO:<" + mail + ">\r\n").encode())
				# time.sleep(sleep_time)
				data = receiveOneLine(smtpSocket)
				print('Received', repr(data))
			#DATA
			subject = str(newEmail.cleaned_data['subject'])
			msgData = str(newEmail.cleaned_data['data'])
			smtpSocket.sendall(bytes("DATA\r\n".encode()))
			# time.sleep(sleep_time)
			data = receiveOneLine(smtpSocket)
			print('Received', repr(data))
			# Send message.
			data = "To: "+newEmail.cleaned_data['toEmail']+"\nFrom: "+loggedEmail+"\nSubject: "+subject+"\n\n"+msgData+"\r\n"
			smtpSocket.sendall(data.encode())
			# time.sleep(sleep_time)
			#. (Enviar .)
			smtpSocket.sendall(bytes("\r\n.\r\n".encode()))
			# time.sleep(sleep_time)
			data = receiveOneLine(smtpSocket)
			print('Received', repr(data))
			#QUIT
			smtpSocket.sendall(bytes("QUIT\r\n".encode()))
			# time.sleep(sleep_time)
			data = receiveOneLine(smtpSocket)
			print('Received', repr(data))
			smtpSocket.close() # Este close no se si va a ser necesario, porque el server cierra la conexion
		# except:
		# 	smtpSocket.close()

		return redirect("createEmailPage")

def loginPage(request):
	global loggedEmail
	global loggedPassword
	if(request.method == 'GET'):
		return render(
			request,
			'webapp/login.html',
			{
				'userForm': UserForm()
			}
		)
	else:
		user = UserForm(request.POST)
		if user.is_valid():
			loggedEmail = user.cleaned_data['email']
			loggedPassword = user.cleaned_data['password']
			print("loggedEmail", loggedEmail)
			print("loggedPassword", loggedPassword)

			localEmails = list(dbclient.mailClient.emails.find({"RCPTTO": loggedEmail}))
			print("localEmails", localEmails)

			return redirect('inboxPage')
