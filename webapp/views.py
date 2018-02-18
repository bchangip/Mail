# -*- coding: utf-8 -*-
# universidad del Valle de Guatemala
from __future__ import division
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
import registration.signals
from .models import EmailForm, UserForm
from django.forms import modelformset_factory
import time
import socket
from pymongo import MongoClient

dbclient = MongoClient('localhost', 27017)

SMTPHOST = "localhost"
SMTPPORT = 2407

POP3HOST = SMTPHOST
POP3PORT = 2408


sleep_time = 0.1


loggedEmail = ""
loggedPassword = ""


def inboxPage(request):
	global loggedEmail
	global loggedPassword
	if loggedEmail == "":
		return redirect("loginPage")

	# Aqui deberia ir el codigo de POP3, los correos que vengan del server guardarlos en mongo
	pop3Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	pop3Socket.connect((POP3HOST, POP3PORT))
	data = pop3Socket.recv(1024).decode()
	print('Received', repr(data))
	pop3Socket.sendall(bytes(str("USER "+loggedEmail).encode()))
	time.sleep(sleep_time)
	data = pop3Socket.recv(1024).decode()
	print('Received', repr(data))
	pop3Socket.sendall(bytes(str("PASS "+loggedPassword).encode()))
	time.sleep(sleep_time)
	data = pop3Socket.recv(1024).decode()
	print('Received', repr(data))
	pop3Socket.sendall(bytes(str("LIST").encode()))
	mailIndices = []
	time.sleep(sleep_time)
	# data = pop3Socket.recv(1024)
	# while(data != b'.'):
	# 	mailIndices.append(data)
	# 	print('Received', repr(data))
	# 	data = pop3Socket.recv(1024)
	# print("Mail indices", mailIndices)
	newMails = []
	while len(newMails) == 0 or (newMails[-1] != '.'):
		newMails.extend(pop3Socket.recv(1024).decode().split("\r\n"))
		if newMails[-1] == '':
			newMails = newMails[:-1]
		print("newMails", newMails)
	# print("newMails", newMails)
	newMails = newMails[1:-1]
	print("newMails", newMails)
	for newMail in newMails:
		pop3Socket.sendall(bytes(str("RETR "+newMail).encode()))
		newMailBuffer = []
		while len(newMailBuffer) == 0 or (newMailBuffer[-1] != '.'):
			newMailBuffer.extend(pop3Socket.recv(1024).decode().split("\r\n"))
			if newMailBuffer[-1] == '':
				newMailBuffer = newMailBuffer[:-1]
		newMailBuffer = newMailBuffer[:-1]
		newMailBuffer = "\n".join(newMailBuffer)
		print("newMail", newMailBuffer)
		dbclient.mailClient.emails.insert({"DATA": newMailBuffer})

		pop3Socket.sendall(bytes(str("DELE "+newMail).encode()))
		response = pop3Socket.recv(1024).decode()
		print("DELE response", response)
	pop3Socket.sendall(bytes(str("QUIT").encode()))
	localEmails = list(dbclient.mailClient.emails.find())
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
		try:
			newEmail = EmailForm(request.POST)
			if newEmail.is_valid():
				print(newEmail.cleaned_data['toEmail'])
				print(newEmail.cleaned_data['data'])

				smtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				smtpSocket.connect((SMTPHOST, SMTPPORT))
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				smtpSocket.sendall(b'HELO uvg.mail')
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))

				#MAIL FROM
				command = "MAIL FROM: <" + loggedEmail + ">"
				# print (command)
				smtpSocket.sendall(command.encode())
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				#RCPT TO
				# print (newEmail.cleaned_data['toEmail'].split(','))
				for mail in newEmail.cleaned_data['toEmail'].split(','):
					print (mail)
					smtpSocket.sendall(("RCPT TO: <" + mail + ">").encode())
					time.sleep(sleep_time)
					data = smtpSocket.recv(1024)
					print('Received', repr(data))
				#DATA
				msgData = str(newEmail.cleaned_data['data'])
				smtpSocket.sendall(b'DATA')
				time.sleep(sleep_time)
				data = smtpSocket.recv(1024)
				print('Received', repr(data))
				# Send message.
				smtpSocket.sendall(msgData.encode())
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
