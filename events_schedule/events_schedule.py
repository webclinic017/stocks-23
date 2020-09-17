# email libs
import ssl
import pandas as pd
from urllib import request
from utils.sql_utils import SQL		
pd.options.mode.chained_assignment = None  # default='warn'

def scrape_data():
	table = crawlData()
	additional_stocks=table[1]=='Cổ phiếu thưởng'
	additional_stocks = table[additional_stocks]
	additional_stocks[5]= additional_stocks[5].apply(getAdditionalStockCount)
	additional_stocks[4]= additional_stocks[4].apply(convertToPercentage)
	for index, row in additional_stocks.iterrows():
		if row[5] >0:
			additional_stocks.at[index, 'percentage'] = (row[5]/row[4])/(row[5] + row[5]/row[4])
		else:
			additional_stocks.at[index, 'percentage'] = 1 - row[4]
	database = SQL()
	database.insertCalendarEvent(additional_stocks)
	table[0]= '<a href="https://finance.vietstock.vn/'+table[0]+'/TS5-co-phieu.htm">'+table[0]+'</a>'
	table = str(table.to_html())
	table = table.replace("&lt;","<")
	table = table.replace("&gt;",">")
	# sendEmail(table, "Stock Calendar Event")

def crawlData():
	url = "https://www.cophieu68.vn/events.php"
	context = ssl._create_unverified_context()
	response = request.urlopen(url, context=context)
	html = response.read()
	df = pd.read_html(html)[1]
	for i in range(2,11):
		url = f'https://www.cophieu68.vn/events.php?currentPage={i}&stockname=&event_type='
		context = ssl._create_unverified_context()
		response = request.urlopen(url, context=context)
		html = response.read()
		df = pd.concat([df, pd.read_html(html)[1]])
	return df

def convertToPercentage(x):
	numbers=str(x).split("/")
	return int(numbers[1])/int(numbers[0])

def getAdditionalStockCount(x):
	count = x.split(" ")[-1].replace(",","")
	return int(count)
# schedule.every().day.at("08:30").do(scrape_data)
# while True:
# 	schedule.run_pending()
# 	time.sleep(1)
