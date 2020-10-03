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
from utils.crawler_utils import get_html_data
import ta 


def generate_plot_fig(ticker):
    database = SQL()
    df = database.getStockData(ticker, 200).sort_values(by='date', ascending=True).set_index('date')
    rsi_data = ta.momentum.RSIIndicator(df['close']).rsi()
    bollingers_data = ta.volatility.BollingerBands(df['close'])
    
    # bollingers_data = bollingerbands(stockprices)
    # rsi_data = rsi(stockprices)
    
    # filter overbuy
    # latest_b = stockprices.tail(1).iloc[0]
    # latest_r = rsi_data.tail(1).iloc[0]
    # if (latest_b['close'] > latest_b['Upper'] or latest_b['close'] > (latest_b['Upper'] +latest_b['MA20'])/2) \
    # and latest_r['close'] >= 70 :
        # logging.info(f"{ticker} is overbought")
        # return None
    logging.debug(f"Generate Charts for {ticker}")
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
            xrotation=0,
            # figscale=1.1,figratio=(8,5),
            # title=f"\n{ticker}",
            savefig=f"{ticker}.png"
            )
    fig.xlabel=f"{ticker}"
    fig.savefig(f'{ticker}.png')
    return 1