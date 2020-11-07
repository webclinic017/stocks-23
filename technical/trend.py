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

filters = ['sma']


def sma_signal_filter(ticker, df, short_value, long_value):
    sma_df = pd.DataFrame(
        data=ta.trend.sma_indicator(df['close'], n=short_value))
    sma_df['sma_short'] = sma_df['sma_' + str(short_value)]
    sma_df['sma_long'] = ta.trend.sma_indicator(df['close'], n=long_value)
    sma0 = sma_df.tail(1)
    sma1 = sma_df.tail(2).head(1)
    if ((sma0['sma_short'] > sma0['sma_long']).iloc[0]
            and (sma1['sma_short'] < sma1['sma_long']).iloc[0]):
        logging.info(f'{ticker} SMA requirement met')
        return sma_df.drop('sma_' + str(short_value), 1)
    return None


def adx_signal_filter(ticker, df):
    adx_data = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
    adx_df = pd.DataFrame(data=adx_data.adx_neg())
    adx_df['adx_pos'] = adx_data.adx_pos()
    adx_df['ADX'] = adx_data.adx()
    adx = adx_df.tail(1)
    if (adx['adx_pos'] < adx['adx_neg']).iloc[0]:
        return None
    logging.info(f'{ticker} ADX requirement met')
    return adx_df


def signal_filter(ticker, df, filters):
    # identify uptrend
    dfs = []
    for flt in filters:
        if flt == 'sma':
            dfs.append(sma_signal_filter(ticker, df, 10, 20))
        if flt == 'adx':
            dfs.append(adx_signal_filter(ticker, df))

    # try:
    for df in dfs:
        if type(df) == type(None):
            return None
        # if None == df:
        # return None
    logging.info("Technical Indicator Requirement met")
    return dfs
    # except Exception as e:
    # logging.error(str(e))
    # return None


def generate_plot_fig(ticker):
    """
    identify entry & exit using MA crossover & DMI 
    """
    database = SQL()
    df = database.getStockData(ticker, 60).sort_values(
        by='date', ascending=True).set_index('date')
    # get technical data
    dfs = signal_filter(ticker, df, filters)
    # not generating graph if not a buy signal
    if dfs == None:
        return None

    fig = mpf.figure(style='yahoo', figsize=(10, 6))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(3, 2, 6)

    apd = [
        mpf.make_addplot(dfs[0], alpha=1, ax=ax1, width=1),
        mpf.make_addplot(ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx(), ax=ax2, width=1)
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
