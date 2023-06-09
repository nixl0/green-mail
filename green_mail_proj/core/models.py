from django.db import models


class Account(models.Model):
    email = models.CharField(max_length=200)
    password = models.CharField(max_length=200) # TODO temporary solution
    imap_host = models.CharField(max_length=100)
    imap_port = models.CharField(max_length=5)
    smtp_host = models.CharField(max_length=100, null=True)
    smtp_port = models.CharField(max_length=5, null=True)
    pop3_host = models.CharField(max_length=100, null=True)
    pop3_host = models.CharField(max_length=5, null=True)


class Email(models.Model):
    sender_email = models.CharField(max_length=100)
    recipients_email = models.CharField(max_length=2048)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    date_sent = models.DateTimeField()