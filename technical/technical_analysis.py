import pandas as pd
from ta.trend import ADXIndicator
from ta.volatility import BollingerBands
from utils.sql_utils import SQL
from utils.stock_data_utils import filterStocks
from datetime import datetime, timedelta
import logging
import base64
from utils.file_utils import deleteFile
from utils.email_utils import sendEmail
from fundamental.fundamental_analysis import get_fundamental_data
import warnings
from technical import trend, non_trend
import numpy as np
warnings.filterwarnings('ignore')


def array_trending(array, length):
    ret = np.cumsum(array, dtype=float)
    ret[length:] = ret[length:] - ret[:-length]
    ar_value = ret[length - 1:] / length
    return np.all(np.diff(ar_value) > 0)


def is_stock_trending(ticker):

    database = SQL()
    # get stock data ADX
    df = database.getStockData(ticker, 50).sort_values(
        by='date', ascending=True).set_index('date')
    adx = ADXIndicator(df['high'], df['low'], df['close']).adx().tail(14)
    adx_ar = adx.to_numpy()
    adx_above_30 = 0
    adx_above_20 = 0
    for i in adx_ar:
        if i > 20:
            adx_above_20 += 1
            if i > 30:
                adx_above_30 += 1

    # under_20_count = 0
    # a1 = adx.tail(1).iloc[0]
    # a2 = adx.tail(2).head(1).iloc[0]
    """ 
    determining if the stock not trending
    1. adx <20
    2. adx in range (20,30) && adx trailling down
    """
    return (adx_above_30 > 5 \
            or (array_trending(adx_ar, len(adx_ar)) and adx_above_20 > 10))


def start_analysis():
    sector_list = filterStocks()
    non_trend_mail = """
        <table>
            <tr>
                <th>Sector</th>
                <th>Ticker</th>
                <th>Graphs</th>
                <th>Company Data</th>
            </tr>
    """
    trending_mail = """
        <table>
            <tr>
                <th>Sector</th>
                <th>Ticker</th>
                <th>Graphs</th>
                <th>Company Data</th>
            </tr>
    """
    for sector in sector_list:
        trending_ticker = []
        non_trending_ticker = []
        ticker_list = sector_list[sector]['ticker'].tolist()
        for ticker in ticker_list:
            try:
                if is_stock_trending(ticker) is False:
                    non_trending_ticker.append(ticker)
                else:
                    trending_ticker.append(ticker)
            except Exception as e:
                logging.error(str(e))
                continue
        if len(trending_ticker) > 0:
            trending_mail += buildEmailContent(sector, trending_ticker, True)
        if len(non_trending_ticker) > 0:
            non_trend_mail += buildEmailContent(sector, non_trending_ticker,
                                                False)
    if non_trend_mail.count('td') > 2:
        sendEmail(
            non_trend_mail,
            f"[{datetime.now().strftime('%Y-%m-%d')}][Non-Trending] Market Technical Analysis"
        )
        file = open(
            f"[{datetime.now().strftime('%Y-%m-%d')}][Non-Trending] Market Technical Analysis.html",
            'a+')
        file.write(non_trend_mail)
    if trending_mail.count('td') > 2:
        sendEmail(
            trending_mail,
            f"[{datetime.now().strftime('%Y-%m-%d')}][Trending] Market Technical Analysis"
        )
        file = open(
            f"[{datetime.now().strftime('%Y-%m-%d')}][Trending] Market Technical Analysis.html",
            'a+')
        file.write(trending_mail)


#delete generated images
    deleteFile('png', '.')


def generateGraph(sector, ticker, is_trending):
    """
    output a html table row 
    """
    if is_trending:
        chart = trend.generate_plot_fig(ticker)
    else:
        chart = non_trend.generate_plot_fig(ticker)

    if (chart is None):
        return ""
    company_data = get_fundamental_data(ticker)
    if company_data is None:
        return ""

    logging.info(f"generate graph {ticker}, is_trending: {is_trending}")

    encoded = base64.b64encode(open(f"{ticker}.png", 'rb').read()).decode()
    html_str = f"""
    <tr>
        <td>{sector}</td>
        <td>
            <a href="https://finance.vietstock.vn/{ticker}/TS5-co-phieu.htm">{ticker}</a>
        </td>
        <td>
            <img src="data:image/png;base64,{encoded}">
        </td>
        <td>
        <p>{company_data}</p>
        </td>
    </tr>
    """
    return html_str


def buildEmailContent(sector, ticker_list, is_trending):
    analysis_type = "Trending" if is_trending else "Non-Trending"
    # logging.info(
        # f"Generate charts for {sector}, type {analysis_type}, list size {len(ticker_list)}"
    # )
    #chunk ticker_list into smaller list for ease of mailing
    # n = 30
    # i = 1
    # ticker_lists = [
    # ticker_list[i:i + n] for i in range(0, len(ticker_list), n)
    # ]
    html_body = ""
    for ticker in ticker_list:
        html_body = html_body + generateGraph(sector, ticker, is_trending)

        # if html_body.count('td') > 2:
        #     file = open(
        #         f"[{datetime.now().strftime('%Y-%m-%d')}][{analysis_type}] Market Technical Analysis.html",
        #         'a+')
        #     file.write(html_body)
        #     sendEmail(
        #         html_body,
        #         f"[{datetime.now().strftime('%Y-%m-%d')}][{analysis_type}] Market Technical Analysis.html",
        #     )

    # logging.info(
    #     f"Sector {sector}, type {analysis_type}, buy signals count: {html_body.count('tr')/2}"
    # )
    return html_body