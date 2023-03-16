from django.http import HttpResponse
from django.shortcuts import render
import smtplib
import imaplib
import email as em

def home(request):
    return render(request, 'home.html');

def add(request):
    if request.method == 'GET':
        return render(request, 'add.html')
    elif request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        smtp_host = request.POST.get('smtp_host')
        smtp_port = request.POST.get('smtp_port')
        imap_host = request.POST.get('imap_host')
        imap_port = request.POST.get('imap_port')

        email_list = login(email, password, imap_host, imap_port)

        return HttpResponse(f'{email_list}')
    
def login(email, password, imap_host, imap_port = 993):
    mail = imaplib.IMAP4_SSL(imap_host, imap_port)
    mail.login(email, password)
    mail.select('inbox')

    _, data = mail.search(None, 'ALL')

    email_list = []
    for num in data[0].split():
        _, data = mail.fetch(num, '(RFC822)')
        # email_list.append(data[0][1])

        # Parse the email message into a Message object
        email_message = em.message_from_bytes(data[0][1])
        # Extract the email message body as a string

        # email_body = ""
        # if email_message.is_multipart():
        #     for payload in email_message.get_payload():
        #         if payload.get_content_type == 'text/html':
        #             email_body += payload.get_payload(decode=True).decode()
        # else:
        #     email_body = email_message.get_payload(decode=True).decode()

        # email_list.append(email_body)

        email_data = {
            'num': num,
            'from': email_message.get('From'),
            'to': email_message.get('To'),
            'bcc': email_message.get('BCC'),
            'date': email_message.get('Date'),
            'subject': email_message.get('Subject')
        }

        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                email_data['content'] = part.as_string()
            elif part.get_content_type() == 'text/html':
                try:
                    html_content = part.get_payload(decode=True).decode()
                    
                    try:
                        html_content = part.get_payload(decode=True).decode('iso-8859-1')
                    except UnicodeDecodeError:
                        raise
                except UnicodeDecodeError:
                    html_content = 'Failed to decode HTML content'

            email_data['html_content'] = html_content

        email_list.append(email_data)

    mail.close()

    return email_list