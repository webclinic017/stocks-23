import requests
import urllib.request
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
import zipfile
import os 
import glob
from sqlalchemy import create_engine
import schedule
import logging
logging.basicConfig(filename='bollinger.log', level = logging.INFO)
class SQL():
    user = 'root'
    pw = 'oracle_4U'
    host = 'localhost'
    db = 'stocks'
    table = 'data'
    engine = None
    
    def __init__(self):
        self.engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}".format(user=self.user,pw=self.pw,host=self.host,db=self.db))
    
    def insert(self, dataframe):
        dataframe.to_sql(self.table, con = self.engine, if_exists = 'append', chunksize=100)
    
    def getStockData(self, ticker, timelimit):
        logging.debug(f"Get stock data for {ticker}")
        return pd.read_sql_query(f"""
            select ticker, date, close 
            from {self.table} 
            where ticker = '{ticker}' 
            order by date desc 
            limit {timelimit}""", con=self.engine)
    
    def getLatestData(self):
        logging.debug("Get latest stock data")
        return pd.read_sql_query(f"""
            select ticker 
            from {self.table} 
            where date = (select distinct date from data order by date desc limit 1)
            and volume >100000
            and length(ticker) =3
            """, con = self.engine)
    
def insertData(time_offset):
    logging.info(f"Insert stock into database with time offset={time_offset}")
    if (time_offset is not None):
        date = datetime.now() - timedelta(time_offset)
    else:
        date = datetime.now()
    # run if it's not weekend
    if (date.weekday() >4):
        return 
    # build URL
    date_yyyymmdd = date.strftime('%Y%m%d')
    date_ddmmyyyy = date.strftime('%d%m%Y')
    url = f"http://images1.cafef.vn/data/{date_yyyymmdd}/CafeF.SolieuGD.Raw.{date_ddmmyyyy}.zip"
    logging.debug(f"Data URL: {url}")
    # download file
    try:
        logging.info("Download file")
        urllib.request.urlretrieve(url,"data.zip")
    except:
        logging.error("Download failed")
        return 
    logging.info("Unzip downloaded file")
    with zipfile.ZipFile('./data.zip', 'r') as zip_ref:
        zip_ref.extractall('.')
    files = glob.glob('./**.csv')
    database = SQL()
    for file in files:
        df = pd.read_csv(file, header=0, parse_dates=['<DTYYYYMMDD>'])
        df = df.rename(columns={
            "<Ticker>":"ticker", 
            "<DTYYYYMMDD>":"date", 
            "<Open>":"open",
            "<High>":"high",
            "<Low>":"low", 
            "<Close>":"close", 
            "<Volume>":"volume"})
        try:
            logging.info(f"Insert {file} into database")
            database.insert(df)
        except:
            logging.error("Error insert to db")
    deleteFile(".csv")

def deleteFile(file_type):
    logging.info(f"Delete files of type \"{file_type}\"")
    directory = "."
    files = os.listdir(directory)
    filtered_files = [file for file in files if file.endswith(file_type)]
    for file in filtered_files:
        file_path = os.path.join(directory, file)
        os.remove(file_path)

def filterStocks():
    logging.info("Filter stocks")
    database = SQL()
    stock_filter = database.getLatestData()['ticker'].tolist()
    return stock_filter

def bollingerbands(ticker):
    logging.debug(f"Generate Bollinger Bands chart for {ticker}")
    database = SQL()
    stockprices = database.getStockData(ticker, 70).sort_values(by='date', ascending=True)
    stockprices = stockprices.set_index('date')
    stockprices['MA20'] = stockprices['close'].rolling(window=20).mean()
    stockprices['20dSTD'] = stockprices['close'].rolling(window=20).std() 
    stockprices['Upper'] = stockprices['MA20'] + (stockprices['20dSTD'] * 2)
    stockprices['Lower'] = stockprices['MA20'] - (stockprices['20dSTD'] * 2)
    latestPrice = stockprices.tail(1).iloc[0]
    latestClose = latestPrice['close']
    latestUpper = latestPrice['Upper']
    latestMA = latestPrice['MA20']
    # filter out stock that are:
    # 1. close > upper => overbuy
    # 2. close > (MA20 +upper)/2 => near overbuy/stop profit point
    if (latestClose > latestUpper or latestClose > (latestUpper+latestMA)/2):
        logging.info(f"{ticker} is in/near overbuy territory, filtered out")
        return None
    stockprices[['close','MA20','Upper','Lower']].plot(figsize=(10,4))
    plt.grid(True)
    plt.title(ticker + ' Bollinger Bands')
    plt.axis('tight')
    plt.ylabel('Price')
    plt.savefig(f'{ticker}.png', bbox_inches='tight')

def generateGraphs():
    logging.info('Generate bollinger graphs')
    if (datetime.now().weekday() >4):
        return None
    ticker_list = filterStocks()
    logging.info(f"initial filter (volume filter): {len(ticker_list)}")
    for ticker in ticker_list:
        bollingerbands(ticker)
    logging.info(f"Generation done for {datetime.now()}")

generateGraphs()

# schedule.every().day.at("20:00").do(insertData(0))
# schedule.every().day.at("21:30").do(generateGraphs())
# while True:
    # schedule.run_pending()
    # time.sleep(1)
