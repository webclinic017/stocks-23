from datetime import datetime, timedelta
import zipfile
import requests
import urllib.request
from utils.sql_utils import SQL     
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

def filterStocks():
    logging.info("Filter stocks")
    database = SQL()
    stock_filter = database.getLatestData()['ticker'].tolist()
    return stock_filter

# def adjustStockPrice(ticker, from_date, percent):
    # calendar_table = 'stock_adjust_calendar'

