# email libs
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendEmail(message_body, subject):
    sender = "hieund2102@gmail.com"
    receiver = sender
    password = "oracle_4U"
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver
    part = MIMEText(message_body, "html")
    message.attach(part)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
        server.login(sender, password)
        server.sendmail(sender,receiver, message.as_string())