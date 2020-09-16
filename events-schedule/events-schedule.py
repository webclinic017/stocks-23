# email libs
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# cron libs
import schedule
import time 
import pandas as pd
from urllib import request

def sendEmail(message_body):
	sender = "hieund2102@gmail.com"
	receiver = sender
	password = "oracle_4U"
	message = MIMEMultipart("alternative")
	message["Subject"] = "Stocks Calendar Event"
	message["From"] = sender
	message["To"] = receiver
	part = MIMEText(message_body, "html")
	message.attach(part)

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
		server.login(sender, password)
		server.sendmail(sender,receiver, message.as_string())
def scrape_data():
	url = 'https://www.cophieu68.vn/events.php'
	context = ssl._create_unverified_context()
	response = request.urlopen(url, context=context)
	html = response.read()
	table = pd.read_html(html)[1]
	# table['extra'] = table[0]
	table[0]= '<a href="https://finance.vietstock.vn/'+table[0]+'/TS5-co-phieu.htm">'+table[0]+'</a>'
	table = str(table.to_html())
	table = table.replace("&lt;","<")
	table = table.replace("&gt;",">")
	print(table)
	# &gt;VC7&lt; /a&gt;
	# print(table.to_html(escapse=False))
	sendEmail(table)

schedule.every().day.at("08:30").do(scrape_data)
while True:
	schedule.run_pending()
	time.sleep(1)
