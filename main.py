import events_schedule.events_schedule as stock_schedule
from utils.sql_utils import SQL
import logging
from technical.bollinger import buildEmailContent as sendBollingerGraphs
from technical.bollinger import bollingerbands
from utils.stock_data_utils import insertData
import schedule
log_format="[%(filename)s:%(lineno)s - %(funcName)s] %(message)s"
logging.basicConfig(filename='stocks.log', level = logging.INFO, format = log_format)

def main():
	bollingerbands('AGR')
	# schedule.every().day.at("08:30").do(stock_schedule.scrape_data)
	# schedule.every().day.at("21:00").do(insertData(0))
	# schedule.every().day.at("21:30").do(sendBollingerGraphs())

if __name__ == '__main__':
	main()
