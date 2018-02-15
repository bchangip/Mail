from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'email/', views.createEmailPage, name='createEmailPage'),
	url(r'inbox/', views.inboxPage, name='inboxPage'),
	url(r'login/', views.loginPage, name='loginPage'),
    url(r'^$', views.loginPage, name='loginPage'),
]