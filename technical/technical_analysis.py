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
def rsi(stockprices):
    # df = stockprices
    delta = stockprices['close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    # Calculate the SMA
    roll_up = up.rolling(window=14).mean()
    roll_down = down.abs().rolling(window=14).mean()
    # Calculate the RSI based on SMA
    RS = roll_up / roll_down
    RSI = 100.0 - (100.0 / (1.0 + RS))
    df = pd.DataFrame(RSI)
    df[['upper', 'lower', 'middle']] = [70, 30, 50]
    return df


def bollingerbands(stockprices):
    stockprices['MA20'] = stockprices['close'].rolling(window=20).mean()
    stockprices['20dSTD'] = stockprices['close'].rolling(window=20).std() 
    stockprices['Upper'] = stockprices['MA20'] + (stockprices['20dSTD'] * 2)
    stockprices['Lower'] = stockprices['MA20'] - (stockprices['20dSTD'] * 2)
    bollingers = stockprices[['MA20', 'Upper', 'Lower']]
    return bollingers

def generate_plot_fig(ticker):
    database = SQL()
    stockprices = database.getStockData(ticker, 200).sort_values(by='date', ascending=True).set_index('date')
    bollingers_data = bollingerbands(stockprices)
    rsi_data = rsi(stockprices)
    
    # filter overbuy
    latest_b = stockprices.tail(1).iloc[0]
    latest_r = rsi_data.tail(1).iloc[0]
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
    company_data= get_html_data(f"https://finance.vietstock.vn/{ticker}/tai-chinh.htm").replace('\n','<br>')
    html_str = f"""
    <tr>
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

def buildEmailContent():
    # get tickers list filtered by volume
    sector_list = filterStocks()
    for sector in sector_list:
        ticker_list = sector_list[sector]['ticker'].tolist()

        #chunk ticker_list into smaller list for ease of mailing
        n = 30
        i = 1
        ticker_lists = [ticker_list[i:i+n] for i in range(0, len(ticker_list), n)]
        for sublist in ticker_lists:
            html_body = """
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Graphs</th>
                    <th>Company Data</th>
                </tr>
            """
            for ticker in sublist:
                html_body = html_body + generateGraph(ticker)
            sendEmail(html_body, f"[{datetime.now().strftime('%Y-%m-%d')}][{sector}] Part {i} Market Technical Analysis")
            i = i + 1
        #delete generated images
        deleteFile('png', '.')
