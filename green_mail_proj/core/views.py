from django.http import HttpResponse
from django.shortcuts import render
import smtplib
import imaplib
import email as em


'''
    Home page
    Initially thru GET shows no mail accounts, but once the user signs into one, loads the messages
'''
def home(request):
    if request.method == 'GET':
        
        return render(request, 'home.html');

    elif request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        smtp_host = request.POST.get('smtp_host')
        smtp_port = request.POST.get('smtp_port')
        imap_host = request.POST.get('imap_host')
        imap_port = request.POST.get('imap_port')

        email_list = login(email, password, imap_host, imap_port)

        return render(request, 'home.html', {
            'email': email,
            'emails': email_list
        })


'''
    Authentication page
'''
def add(request):
    return render(request, 'add.html')


'''
    Logic to sign in and load mail
'''
def login(email, password, imap_host, imap_port = 993):
    mail = imaplib.IMAP4_SSL(imap_host, imap_port)
    mail.login(email, password)
    mail.select('inbox')

    _, data = mail.search(None, 'ALL')

    email_list = []
    for num in data[0].split():
        _, data = mail.fetch(num, '(RFC822)')

        email_message = em.message_from_bytes(data[0][1])

        email_data = {
            'num': num.decode(),
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
                # try:
                #     html_content = part.get_payload(decode=True).decode('utf-8')

                #     try:
                #         html_content = part.get_payload(decode=True).decode('iso-8859-1')
                #     except UnicodeDecodeError:
                #         raise
                # except UnicodeDecodeError:
                #     html_content = 'Failed to decode HTML content'

                try:
                    html_content = part.get_payload(decode=True).decode('iso-8859-1')
                except UnicodeDecodeError:
                    html_content = 'Failed to decode HTML content'

            email_data['html_content'] = html_content

        email_list.append(email_data)

    mail.close()

    return email_list


def view_message(request):
    pass