import pandas as pd
from ta.trend import ADXIndicator
from sql_utils import SQL 
from utils.stock_data_utils import filterStocks

def is_stock_trending(ticker):
	database = SQL()
	# get stock data 
	df = database.getStockData(ticker, 200).sort_values(by='date', ascending=True).set_index('date')
	df = ADXIndicator(df['high'],df['low'], df['close'], fillna=True)

def filter_trend():
	trending_ticker = []
	non_trending_ticker = []
	sector_list = filterStocks()
	for sector in sector_list:
		ticker_list = sector_list[sector]['ticker'].tolist()

