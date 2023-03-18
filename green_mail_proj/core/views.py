from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import smtplib
import imaplib
import email as em
import base64
import ssl
from core.models import Email, Account
from django.db import connection
from dateutil import parser


def home(request):
    if request.method == 'GET':
        return render(request, 'home.html')
    elif request.method == 'POST':
        email_address = request.POST.get('email')
        password = request.POST.get('password')
        smtp_host = request.POST.get('smtp_host')
        smtp_port = request.POST.get('smtp_port')
        imap_host = request.POST.get('imap_host')
        imap_port = request.POST.get('imap_port')

        # check connections
        imap_connection, imap_ex = check_imap_connection(email_address, password, imap_host, imap_port)
        if not imap_connection:
            return render(request, 'error.html', {
                'message': 'Не получилось подключиться к серверу IMAP.',
                'exception': imap_ex
                })
        smtp_connection, smtp_ex = check_smtp_connection(email_address, password, smtp_host, smtp_port)
        if not smtp_connection:
            return render(request, 'error.html', {
                'message': 'Не получилось подключиться к серверу SMTP.',
                'exception': smtp_ex
                })

        # signing in
        messages_list = load_imap_messages(email_address, password, imap_host, imap_port)

        # saving account credentials
        # deletes the contents of the Account table and restarts the index sequence
        Account.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="core_account"')
        # adds account
        account = Account(
            email=email_address,
            password=password,
            imap_host=imap_host,
            imap_port=imap_port,
            smtp_host=smtp_host,
            smtp_port=smtp_port
        )

        account.save()


        # loading messages into our local db cache
        # deletes the contents of the Email table and restarts the index sequence
        Email.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="core_email"')
        # does the loading itself
        for message in messages_list:
            email = Email(
                sender_email=message['from'],
                recipients_email=message['to'],
                subject=message['subject'],
                body=message['body'],
                date_sent=parser.parse(message['date']).strftime('%Y-%m-%d %H:%M:%S')
            )

            email.save()

        return render(request, 'home.html', {
            'messages': messages_list,
            'email_address': email_address
        })


def authenticate(request):
    return render(request, 'authentication.html')


def check_imap_connection(email_address, password, imap_host, imap_port):
    try:
        imap_server = imaplib.IMAP4_SSL(imap_host, imap_port)
        imap_server.login(email_address, password)
        imap_server.select('INBOX')
        imap_server.close()
        imap_server.logout()
        return True, None
    except Exception as e:
        return False, e
    

def check_smtp_connection(email_address, password, smtp_host, smtp_port):
    try:
        smtp_server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl.create_default_context())
        smtp_server.login(email_address, password)
        smtp_server.quit()
        return True, None
    except Exception as e:
        return False, e


def load_imap_messages(email, password, imap_host, imap_port=993):
    # log in to the imap server
    mail = imaplib.IMAP4_SSL(imap_host, imap_port)
    mail.login(email, password)

    # select inbox and load all messages
    mail.select('inbox')
    _, data = mail.search(None, 'ALL')

    # parse messages
    messages_list = []
    for num in data[0].split():
        _, data = mail.fetch(num, '(RFC822)')
        # raw_message = em.message_from_bytes(data[0][1])
        # message = em.message_from_bytes(raw_message)

        raw_message = data[0][1].decode('utf-8')
        message = em.message_from_string(raw_message)

        # decode
        parsed_message_fields = {
            'num': num.decode(),
            'from': decode_base64(message['From']),
            'to': decode_base64(message['Subject']),
            'bcc': message['Bcc'],
            'date': message['Date'],
            'subject': decode_base64(message['Subject']),
        }

        message_body = ''

        # if raw_message.is_multipart():
        #     for payload in raw_message.get_payload():
        #         if payload.get_content_type() == 'text/html':
        #             try:
        #                 message_body += payload.get_payload(decode=True).decode()
        #             except UnicodeDecodeError:
        #                 message_body = 'Failed to decode HTML content'
        #         else:
        #             message_body = raw_message.get_payload()

        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                message_body = part.get_payload()
            elif part.get_content_type() == 'text/html':
                # message_body = 'HTML'
                message_body = part.get_payload(decode=True).decode()

        parsed_message_fields['body'] = message_body

        messages_list.append(parsed_message_fields)

    mail.close()

    return messages_list


def decode_base64(encoded_str):
    decoded_str = ''
    if "=?utf-8?b?" in encoded_str:
        encoded_str_parts = encoded_str.split("=?utf-8?b?")
        for part in encoded_str_parts:
            if part:
                decoded_part = base64.b64decode(part)
                decoded_str += decoded_part.decode('utf-8')
    else:
        decoded_str = encoded_str

    return decoded_str


def show(request, num):
    email = Email.objects.get(id=num)
    return render(request, 'message.html', {
        'message': email
    })


def compose(request):
    return render(request, 'compose.html')


def send(request):
    recipient = request.POST.get('recipient')
    subject = request.POST.get('subject')
    body = request.POST.get('body')

    account = Account.objects.get(id=1)
    email_address = account.email
    password = account.password
    smtp_host = account.smtp_host
    smtp_port = account.smtp_port

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl.create_default_context()) as smtp_server:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_server.login(email_address, password)

            message = MIMEMultipart()
            message['From'] = email_address
            message['To'] = recipient
            message['Subject'] = subject
            message.attach(MIMEText(body, 'html'))

            smtp_server.send_message(message)

        return redirect(home)
    except Exception as e:
        return render(request, 'error.html', {'message': 'Отправить сообщение не удалось', 'exception': e})
