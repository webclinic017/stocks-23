import pandas as pd
from ta.trend import ADXIndicator
from ta.volatility import BollingerBands
from utils.sql_utils import SQL 
from utils.stock_data_utils import filterStocks
from datetime import datetime,timedelta
import logging
import base64
from utils.file_utils import deleteFile
from utils.email_utils import sendEmail
from fundamental.fundamental_analysis import get_fundamental_data
import warnings
from technical import trend,non_trend

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


	
def start_analysis():
	sector_list = filterStocks()
	for sector in sector_list:
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
		if len(trending_ticker) >0: buildEmailContent(sector,trending_ticker,True) 
		if len(non_trending_ticker) >0: buildEmailContent(sector,non_trending_ticker,False) 




def generateGraph(ticker, is_trending):
    """
    generate bollinger graph & URL for ticker detail
    output a html table row 
    """
    logging.info(f"generate graph {ticker}, is_trending: {is_trending}")
    company_data = get_fundamental_data(ticker)

    if company_data is None:
    	return ""
    if is_trending:
    	chart = trend.generate_plot_fig(ticker)
    else:
    	chart = non_trend.generate_plot_fig(ticker)

    if (chart is None):
        return ""
    encoded = base64.b64encode(open(f"{ticker}.png", 'rb').read()).decode()
    html_str = f"""
    <tr>
        <td>
            <a href="https://finance.vietstock.vn/{ticker}/TS5-co-phieu.htm">{ticker}</a>
        </td>
        <td>
            <img src="data:image/png;base64,{encoded}">
        </td>
        <td>
        <p>{company_data}</p>
        </td>
    </tr>
    """
    return html_str

def buildEmailContent(sector,ticker_list,is_trending):
	analysis_type = "Trending" if is_trending else "Non-Trending"
	logging.info(f"Generate charts for {sector}, type {analysis_type}")
    #chunk ticker_list into smaller list for ease of mailing
	n = 30
	i = 1
	ticker_lists = [ticker_list[i:i+n] for i in range(0, len(ticker_list), n)]
	for sublist in ticker_lists:
		html_body = """
        <table>
            <tr>
                <th>Ticker</th>
                <th>Graphs</th>
                <th>Company Data</th>
            </tr>
        """
		for ticker in sublist:
			html_body = html_body + generateGraph(ticker, is_trending)
		sendEmail(html_body, f"[{datetime.now().strftime('%Y-%m-%d')}][{sector}][{analysis_type}] Part {i} Market Technical Analysis")
		i = i + 1
    #delete generated images
	deleteFile('png', '.')

