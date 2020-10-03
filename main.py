# -*- coding: utf-8 -*-

import events_schedule.events_schedule as stock_schedule
from utils.sql_utils import SQL
import logging
from technical.technical_analysis import buildEmailContent as sendTechnicalAnalysis
from technical.technical_analysis import generate_plot_fig
from utils.stock_data_utils import insertData, filterStocks
from utils.crawler_utils import get_child_urls,get_url_data,get_html_data
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

def getTickerData():
	urls = get_child_urls("https://finance.vietstock.vn/chi-so-nganh.htm")
	for url in urls:
		if '/nganh/' in url:
			sector = url.split("/")[-1].split('.')[0]
			# print(sector)
			df = get_url_data(url)
			df = df.drop(df.columns[[0,3,4,5,6]] ,axis=1)
			df['sector']=sector
			pd.set_option('display.max_rows', df.shape[0]+1)
			print(df)

def main():
	database = SQL()
	# dfs = filterStocks()
	# for df in dfs:
		# print(dfs[df])
	# scheduling()
	# generate_plot_fig('AGR')
	# for i in range(6,365):
		# insertData(i)
	stock_schedule.scrape_data()
	# database.adjustPrice()
	# sendTechnicalAnalysis()

if __name__ == '__main__':
	main()
