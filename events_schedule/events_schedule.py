# email libs
import ssl
import pandas as pd
import numpy as np
from urllib import request
from utils.sql_utils import SQL		
from utils.email_utils import sendEmail
import logging
pd.options.mode.chained_assignment = None  # default='warn'

def scrape_data():
	logging.info('Crawl Stock Calendar Events')
	df = crawlData()
	header_filter= df[1]!= 'Loại Sự Kiện'
	df = df[header_filter]
	event_filter = df[1] != 'Phát hành khác'
	df = df[event_filter]
	logging.info('Adjusting stock prices')
	df = calculate_stock_adjustment(df)
	database = SQL()
	database.insertCalendarEvent(df)
	# df[0]= '<a href="https://finance.vietstock.vn/'+df[0]+'/TS5-co-phieu.htm">'+df[0]+'</a>'
	# df = str(df.to_html())
	# df = df.replace("&lt;","<")
	# df = df.replace("&gt;",">")
	# # sendEmail(table, "Stock Calendar Event")

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

def calculate_stock_adjustment(df):
	"""
	calculate stock adjusted price using the following formulae:
	adjusted_close = close / F
	1. cash dividend
		F = (Close + dividend_per_share)/Close
	2. stock dividend
		F = 1 + share_issue_rate
	"""

	# get cash dividend events
	cash_div = df[1]=='Cổ tức bằng tiền'
	cdf=df[cash_div]
	cdf[4]=cdf[4].apply(lambda x: 10 *float(x.replace('%',''))/100)
	cdf[1]='Cash Dividend'
	
	# get stock dividend events
	# ratio display as x/y
	# F = 1 + y/x
	stock_div = df[1]=='Cổ phiếu thưởng'
	sdf =df[stock_div]
	sdf[4]=sdf[4].apply(lambda x: 1 + (int(x.split('/')[1])/int(x.split('/')[0])))
	sdf[1]='Stock Dividend'

	# finalizing data
	df = cdf.append(sdf)
	df = df.drop(df.columns[[5]], axis=1)
	df.columns = ['ticker', 'event', 'date','execution_date', 'detail']
	df['date'] = pd.to_datetime(df['date'])
	df['processed'] =0
	df['execution_date'] = df['execution_date'].replace(np.nan, '', regex=True)
	return df