import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
import logging
import base64
from utils.file_utils import deleteFile
from utils.stock_data_utils import filterStocks
from utils.sql_utils import SQL
from utils.email_utils import sendEmail
def bollingerbands(ticker):
    logging.debug(f"Generate Bollinger Bands chart for {ticker}")
    database = SQL()
    stockprices = database.getStockData(ticker, 200).sort_values(by='date', ascending=True)
    stockprices = stockprices.set_index('date')
    stockprices['MA20'] = stockprices['close'].rolling(window=20).mean()
    stockprices['SMA200'] = stockprices['close'].rolling(window=200).mean()
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
    stockprices[['close','MA20','Upper','Lower','SMA200']].plot(figsize=(7.5,3))
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

def buildEmailContent():
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
        sendEmail(html_body, f"Bollinger Chart {datetime.now()} Part {i}")
        i = i + 1
    #delete generated images
    deleteFile('png', '.')

# schedule.every().day.at("20:00").do(insertData(0))
# schedule.every().day.at("21:30").do(sendEmail())
# while True:
    # schedule.run_pending()
    # time.sleep(1)

# sendEmail()
# insertData(0)
# bollingerbands('SJE')
