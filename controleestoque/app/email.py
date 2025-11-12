from flask_mail import Message
from app import mail

from app import app

from flask import render_template
from app import app

def send_email(subject, recipients, text_body, html_body, sender=None):
    if sender is None:
        sender = app.config['MAIL_DEFAULT_SENDER']
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[YourApp] Reset Your Password',
               sender=app.config['MAIL_DEFAULT_SENDER'],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
