# email libs
import ssl
# cron libs
import schedule
import time 
import pandas as pd
from urllib import request
from utils.sql_utils import SQL		
def scrape_data():
	url = 'https://www.cophieu68.vn/events.php'
	context = ssl._create_unverified_context()
	response = request.urlopen(url, context=context)
	html = response.read()
	table = pd.read_html(html)[1]
	# table['extra'] = table[0]
	# print(table)
	additional_stocks=table[1]=='Cổ phiếu thưởng'
	additional_stocks = table[additional_stocks]
	additional_stocks[4]= additional_stocks[4].apply(convertToPercentage)
	# print(additional_stocks)
	database = SQL()
	database.insertCalendarEvent(additional_stocks)
	table[0]= '<a href="https://finance.vietstock.vn/'+table[0]+'/TS5-co-phieu.htm">'+table[0]+'</a>'
	table = str(table.to_html())
	table = table.replace("&lt;","<")
	table = table.replace("&gt;",">")
	# sendEmail(table, "Stock Calendar Event")

def convertToPercentage(x):
	numbers=str(x).split("/")
	percentage =  1 - (int(numbers[1])/int(numbers[0]))
	return percentage if percentage != 0 else 0.5

# schedule.every().day.at("08:30").do(scrape_data)
# while True:
# 	schedule.run_pending()
# 	time.sleep(1)

scrape_data()