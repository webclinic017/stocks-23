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


def signal_filter(sma_df, adx_df):
    # identify uptrend

    adx = adx_df.tail(1)
    if (adx['adx_pos'] < adx['adx_neg']).iloc[0]:
        return False
    # sma of last closing date
    sma0 = sma_df.tail(1)
    a04 = sma0['sma_4']
    a09 = sma0['sma_9']
    # sma of second to last closing date
    sma1 = sma_df.tail(2).head(1)
    a14 = sma1['sma_4'].iloc[0]
    a19 = sma1['sma_9'].iloc[0]
    if ((sma0['sma_4'] > sma0['sma_9']).iloc[0] and (sma1['sma_4'] < sma1['sma_9']).iloc[0]) \
    :
        logging.info("Technical Indicator Requirement met")
        # print(sma_df)
        return True

    return False


def generate_plot_fig(ticker):
    """
	identify entry & exit using MA crossover & DMI 
	"""
    database = SQL()
    # get technical data
    # SMA
    df = database.getStockData(ticker, 60).sort_values(
        by='date', ascending=True).set_index('date')
    sma = pd.DataFrame(data=ta.trend.sma_indicator(df['close'], n=4))
    sma['sma_9'] = ta.trend.sma_indicator(df['close'], n=9)

    # DMI
    adx_data = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])

    adx_df = pd.DataFrame(data=adx_data.adx_neg())
    adx_df['adx_pos'] = adx_data.adx_pos()
    adx_df['ADX'] = adx_data.adx()
    # not generating graph if not a buy signal
    if not signal_filter(sma, adx_df):
        return None

    fig = mpf.figure(style='yahoo', figsize=(10, 6))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(3, 2, 6)

    apd = [
        mpf.make_addplot(sma, alpha=1, ax=ax1, width=1),
        mpf.make_addplot(adx_df, ax=ax2, width=1)
    ]
    fig.suptitle(ticker)
    mpf.plot(df,
             type='ohlc',
             style='yahoo',
             figsize=(10, 6),
             xrotation=0,
             ax=ax1,
             volume=ax3,
             addplot=apd,
             savefig=f"{ticker}.png")
    fig.savefig(f"{ticker}.png")
    return 1
