import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timedelta
import logging
import base64
from utils.file_utils import deleteFile
from utils.stock_data_utils import filterStocks
from utils.sql_utils import SQL
from utils.email_utils import sendEmail
from utils.crawler_utils import get_html_data
import ta


def signal_filter(ticker, boll_df, rsi_df, close):
    # data for latest closing date
    c0 = close.tail(1).iloc[0]
    b0 = boll_df.tail(1)
    l0 = b0['lband'].iloc[0]
    h0 = b0['hband'].iloc[0]
    m0 = b0['mavg'].iloc[0]
    r0 = rsi_df.tail(1)['rsi'].iloc[0]
    # data for second latest closing date
    c1 = close.tail(2).head(1).iloc[0]
    b1 = boll_df.tail(2).head(1)
    r1 = rsi_df.tail(2).head(1)['rsi'].iloc[0]
    if ((c0 > b0['lband'].iloc[0]) and
        (c1 < b1['lband'].iloc[0])) or (r0 > 30 and r1 < 30):
        logging.info(
            f"{ticker} Technical Indicator Requirement met; Profit range {(h0 - l0) / h0}"
        )
        if (((h0 - l0) / h0) * 100 > 5):
            logging.info("Profitable Range")
            return True


def generate_plot_fig(ticker):
    database = SQL()
    df = database.getStockData(ticker, 90).sort_values(
        by='date', ascending=True).set_index('date')
    rsi_data = ta.momentum.RSIIndicator(df['close']).rsi()
    rsi_data = pd.DataFrame(data=rsi_data)
    # rsi_data[['upper', 'lower', 'middle']] = [70,30,50]

    bollingers_data = ta.volatility.BollingerBands(df['close'])
    bollinger = pd.DataFrame(data=bollingers_data.bollinger_mavg())
    bollinger['hband'] = bollingers_data.bollinger_hband()
    bollinger['lband'] = bollingers_data.bollinger_lband()

    fig = mpf.figure(style='yahoo', figsize=(10, 6))
    ax1 = fig.add_subplot(3, 1, 1)
    ax2 = fig.add_subplot(3, 1, 2)
    ax3 = fig.add_subplot(3, 1, 3)

    if not signal_filter(ticker, bollinger, rsi_data, df['close']):
        return None

    apd = [
        mpf.make_addplot(bollinger, alpha=0.3, ax=ax1),
        mpf.make_addplot(rsi_data, ax=ax2)
    ]
    fig.suptitle(ticker)
    mpf.plot(df,
             type='candle',
             style='yahoo',
             figsize=(10, 6),
             xrotation=0,
             ax=ax1,
             volume=ax3,
             addplot=apd,
             savefig=f"{ticker}.png")
    fig.savefig(f"{ticker}.png")
    return 1