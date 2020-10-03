import pandas as pd
from ta.trend import ADXIndicator
from ta.volatility import BollingerBands
from utils.sql_utils import SQL 
from utils.stock_data_utils import filterStocks
from datetime import timedelta
import warnings

warnings.filterwarnings('ignore')


def is_stock_trending(ticker):
	database = SQL()
	# get stock data ADX
	df = database.getStockData(ticker, 50).sort_values(by='date', ascending=True).set_index('date')
	adx = ADXIndicator(df['high'],df['low'], df['close']).adx().tail(14)
	under_20_count = 0
	# determining if the stock not trending
	# 1. adx <20
	# 2. adx in range (20,30) && adx trailling down
	pre_value = None
	for value in adx.tolist():
		if pre_value is None:
			pre_value = value
		if (value <20):
			under_20_count = under_20_count+1
		elif value in range(20,31) and value<pre_value:
			under_20_count = under_20_count+1
		pre_value = value
	# print(ticker, under_20_count<5)
	return True if under_20_count < 5 else False

def bollinger(ticker):
	database = SQL()
	# get stock data ADX
	df = database.getStockData(ticker, 50).sort_values(by='date', ascending=True).set_index('date')
	boll = BollingerBands(df['close'])
	df['ma'] = boll.bollinger_mavg()
	df['hband'] = boll.bollinger_hband()
	df['lband'] = boll.bollinger_lband()
	high = boll.bollinger_hband_indicator()[-1] ==1
	low = boll.bollinger_lband_indicator()[-1] ==1
	if (high or low):
		print(df)
	return boll
	
def filter_trend():
	sector_list = filterStocks()
	for sector in sector_list:
		print(f'---------{sector}------------')
		trending_ticker = []
		non_trending_ticker = []
		ticker_list = sector_list[sector]['ticker'].tolist()
		for ticker in ticker_list:

			try:
				if is_stock_trending(ticker) is False:
					non_trending_ticker.append(ticker)
				else:
					trending_ticker.append(ticker)
			except:
				continue
		print('trending: ',trending_ticker)
		print('non-trending: ', non_trending_ticker)
