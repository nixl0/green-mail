from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import smtplib
import imaplib
import email as em
import base64



def home(request):
    if request.method == 'GET':
        return render(request, 'home.html')
    elif request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        smtp_host = request.POST.get('smtp_host')
        smtp_port = request.POST.get('smtp_port')
        imap_host = request.POST.get('imap_host')
        imap_port = request.POST.get('imap_port')

        # signing in
        messages_list = load_imap_messages(email, password, imap_host, imap_port)

        # loading messages into our local db cache
        # TODO

        # string = ''
        # for dic in messages_list:
        #     string = string + str(dic['num']) + '<br>'
        #     for key, value in dic:
        #         string = string + f'{str(key)}: {str(value)}' + '<br>'
            
        #     string = string + '<hr>'

        return HttpResponse(messages_list)

def authenticate(request):
    return render(request, 'authentication.html')


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
                message_body = 'HTML'

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