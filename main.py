# from events_schedule.events_schedule import scrape_data as get_stock_calendar
from utils.sql_utils import SQL
import logging
log_format="[%(filename)s:%(lineno)s - %(funcName)s] %(message)s"
logging.basicConfig(filename='stocks.log', level = logging.INFO, format = log_format)
def main():
	# print("test")
	# get_stock_calendar()
	# try:
	database = SQL()
	# print(type(database))
	database.adjustPrice()
	# except Exception as e:
		# print(str(e))

if __name__ == '__main__':
	main()
