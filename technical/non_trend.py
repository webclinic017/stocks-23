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
    df = database.getStockData(ticker, 90).sort_values(by='date', ascending=True).set_index('date')
    rsi_data = ta.momentum.RSIIndicator(df['close']).rsi()
    rsi_data = pd.DataFrame(data=rsi_data)
    rsi_data[['upper', 'lower', 'middle']] = [70,30,50]

    bollingers_data = ta.volatility.BollingerBands(df['close'])
    bollinger = pd.DataFrame(data=bollingers_data.bollinger_mavg())
    bollinger['hband'] = bollingers_data.bollinger_hband()
    bollinger['lband'] = bollingers_data.bollinger_lband()

    fig = mpf.figure(style='yahoo',figsize=(10,6))
    ax1 = fig.add_subplot(3,1,1)
    ax2 = fig.add_subplot(3,1,2)
    ax3 = fig.add_subplot(3,1,3)

    apd = [
        mpf.make_addplot(bollinger, alpha = 0.3,ax = ax1),
        mpf.make_addplot(rsi_data, ax=ax2)
    ]
    fig.suptitle(ticker)
    mpf.plot(df, type='candle',
    		style='yahoo',
    		figsize=(10,6),
            xrotation=0,
            ax = ax1, 
            volume=ax3,
            addplot=apd,
            savefig=f"{ticker}.png"
            )
    fig.savefig(f"{ticker}.png")
    return 1 