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
import base64

# email libs
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
    stockprices[['close','MA20','Upper','Lower']].plot(figsize=(7.5,3))
    plt.grid(True)
    plt.title(ticker + ' Bollinger Bands')
    plt.axis('tight')
    plt.ylabel('Price')
    plt.savefig(f'{ticker}.png', bbox_inches='tight')
    return 1

def generateGraph(ticker):
    """
    generate bollinger graph & URL for ticker detail
    output a html table row 
    """
    logging.info(f"generate graph {ticker}")
    chart = bollingerbands(ticker)
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
    </tr>
    """
    return html_str

def sendEmailConfig(message_body, i):
    sender = "hieund2102@gmail.com"
    receiver = sender
    password = "oracle_4U"
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Bollinger Chart {datetime.now()} Part {i}"
    message["From"] = sender
    message["To"] = receiver
    part = MIMEText(message_body, "html")
    message.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
        server.login(sender, password)
        server.sendmail(sender,receiver, message.as_string())

def sendEmail():
    # get tickers list filtered by volume
    ticker_list = filterStocks()
    #chunk ticker_list into smaller list for ease of mailing
    n = 30
    i = 1
    ticker_lists = [ticker_list[i:i+n] for i in range(0, len(ticker_list), n)]
    for sublist in ticker_lists:
        html_body = """
        <table>
        <th>
        <td>Ticker</td>
        <td>Bollinger</td>
        </th>
        """
        for ticker in sublist:
            html_body = html_body + generateGraph(ticker)
        html_body = html_body+"</table>"
        sendEmailConfig(html_body, i)
        i = i + 1
    #delete generated images
    deleteFile('png')


# schedule.every().day.at("20:00").do(insertData(0))
# schedule.every().day.at("21:30").do(sendEmail())
# while True:
    # schedule.run_pending()
    # time.sleep(1)

sendEmail()
