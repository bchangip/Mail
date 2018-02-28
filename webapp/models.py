from __future__ import unicode_literals

from django.db import models
from django.forms import ModelForm
import django.contrib.postgres.fields as postgresModule

# Create your models here.

class Email(models.Model):
	toEmail = models.CharField(max_length=4096)
	subject = models.CharField(max_length=4096)
	data = models.CharField(max_length=8192)

class EmailForm(ModelForm):
	class Meta:
		model = Email
		fields = ['toEmail', 'subject', 'data']

class User(models.Model):
	email = models.CharField(max_length=100)
	password = models.CharField(max_length=4096)

class UserForm(ModelForm):
	class Meta:
		model = User
		fields = ['email', 'password']
