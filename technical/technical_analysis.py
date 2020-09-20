import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime,timedelta
import logging
import base64
from utils.file_utils import deleteFile
from utils.stock_data_utils import filterStocks
from utils.sql_utils import SQL
from utils.email_utils import sendEmail

def rsi(stockprices):
    df = stockprices
    delta = df['close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    # Calculate the SMA
    roll_up = up.rolling(window=14).mean()
    roll_down = down.abs().rolling(window=14).mean()
    # Calculate the RSI based on SMA
    RS = roll_up / roll_down
    RSI = 100.0 - (100.0 / (1.0 + RS))
    df2 = pd.DataFrame(RSI)
    df2[['upper', 'lower', 'middle']] = [70, 30, 50]
    return df2


def bollingerbands(stockprices):
    stockprices['MA20'] = stockprices['close'].rolling(window=20).mean()
    stockprices['20dSTD'] = stockprices['close'].rolling(window=20).std() 
    stockprices['Upper'] = stockprices['MA20'] + (stockprices['20dSTD'] * 2)
    stockprices['Lower'] = stockprices['MA20'] - (stockprices['20dSTD'] * 2)
    bollingers = stockprices[['MA20', 'Upper', 'Lower']]
    return bollingers

def generate_plot_fig(ticker):
    logging.debug(f"Generate Charts for {ticker}")
    database = SQL()
    stockprices = database.getStockData(ticker, 200).sort_values(by='date', ascending=True).set_index('date')
    bollingers_data = bollingerbands(stockprices)
    rsi_data = rsi(stockprices)
    
    # filter overbuy
    latest_b = stockprices.tail(1).iloc[0]
    latest_r = rsi_data.tail(1).iloc[0]
    if (latest_b['close'] > latest_b['Upper'] or latest_b['close'] > (latest_b['Upper'] +latest_b['MA20'])/2) \
    and latest_r['close'] >= 70 :
        logging.info(f"{ticker} is overbought")
        return None

    fig = mpf.figure(style='yahoo',figsize=(10,6))
    ax1 = fig.add_subplot(3,1,1)
    ax2 = fig.add_subplot(3,1,2)
    ax3 = fig.add_subplot(3,1,3)

    apd = [
        mpf.make_addplot(bollingers_data, alpha = 0.3,ax = ax1),
        mpf.make_addplot(rsi_data, ax=ax2, ylabel = f"{ticker}")
    ]
    logging.info(f"generate charts for {ticker}")
    mpf.plot(stockprices, type='candle', 
        ax = ax1, 
            volume=ax3,
            addplot=apd,
            xrotation=10,
            savefig=f"{ticker}.png"
            )
    fig.savefig(f'{ticker}.png')
    return 1

def generateGraph(ticker):
    """
    generate bollinger graph & URL for ticker detail
    output a html table row 
    """
    logging.info(f"generate graph {ticker}")
    chart = generate_plot_fig(ticker)
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
            <td>Graphs</td>
            </th>
        """
        for ticker in sublist:
            html_body = html_body + generateGraph(ticker)
        html_body = html_body+"</table>"
        sendEmail(html_body, f"[{datetime.date.today()}] Part {i} Market Technical Analysis")
        i = i + 1
    #delete generated images
    deleteFile('png', '.')
