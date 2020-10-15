# -*- coding: utf-8 -*-

import events_schedule.events_schedule as stock_schedule
from utils.sql_utils import SQL
import logging
from technical.technical_analysis import start_analysis
from utils.stock_data_utils import insertData, filterStocks
from utils.crawler_utils import get_child_urls,get_url_data,get_html_data
from fundamental.fundamental_analysis import get_fundamental_data
from backtest.backtest import backtest_trend
import schedule
import pandas as pd
import sys

log_format="[%(filename)s:%(lineno)s - %(funcName)s] %(message)s"

file_handler = logging.FileHandler(filename='stocks.log')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(handlers=handlers, level = logging.INFO, format = log_format)

def scheduling():
	schedule.every().day.at("08:30").do(stock_schedule.scrape_data)
	schedule.every().day.at("21:00").do(insertData,0)
	schedule.every().day.at("21:30").do(sendTechnicalAnalysis)

	database = SQL()
	schedule.every().day.at("21:15").do(database.adjustPrice)



def main():
	database = SQL()
	# get_html_data("https://finance.vietstock.vn/IBC/TS5-co-phieu.htm")
	#for i in range(0,10):
	 #   insertData(i)
	stock_schedule.scrape_data()
	start_analysis()
if __name__ == '__main__':
	main()
