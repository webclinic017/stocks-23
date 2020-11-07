import backtrader as bt
from utils.sql_utils import SQL
# from backtest.custom_strategy import *
import datetime
import os.path
import sys


class Strategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def __init__(self):
        self.dataclose = self.datas[0].close

        # trend filter
        self.adx = bt.indicators.AverageDirectionalMovementIndex(self.datas[0],
                                                                 period=14)

        # trending indicator
        self.sma4 = bt.indicators.MovingAverageSimple(self.datas[0], period=9)
        self.sma9 = bt.indicators.MovingAverageSimple(self.datas[0], period=20)
        self.plusdi = bt.indicators.PlusDirectionalIndicator(self.datas[0],
                                                             period=14)
        self.minusdi = bt.indicators.MinusDirectionalIndicator(self.datas[0],
                                                               period=14)

        # non trending indicator
        self.bolls = bt.indicators.BollingerBands(self.datas[0],
                                                  period=20,
                                                  devfactor=2)
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price {order.executed.price}, Cost {order.executed.value}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(
                    f"SELL EXECUTED, Price {order.executed.price}, Cost {order.executed.value}"
                )

            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f"OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}")

    def buy_indicator(self):
        if (self.adx[0] > 30 or self.adx[0] > self.adx[-1]):
            # trending
            if (self.sma4[0] > self.sma9[0]
                    and self.plusdi[0] > self.minusdi[0]):
                return True
        else:
            # non trending
            if (self.bolls[0] > self.bolls.bot[0]
                    and self.bolls[-1] < self.bolls.bot[-1]):
                return True
        return False

    def sell_indicator(self):
        if (self.adx[0] > 30 or self.adx[0] > self.adx[-1]):
            if (self.sma4[0] < self.sma9[0]
                    and (self.plusdi[0] > self.minusdi[0])):
                return True
        else:
            if (self.bolls[0] < self.bolls.top[0]
                    and self.bolls[-1] > self.bolls.top[-1]):
                return True
        return False

    def next(self):
        if self.order:
            return
        if not self.position:
            if (self.buy_indicator()):
                self.log(f"BUY ORDER; trending? {self.buy_indicator()}")
                self.order = self.buy()
        else:
            if (self.sell_indicator()):
                self.order = self.sell()


def backtest_trend(ticker):
    database = SQL()
    df = database.getStockData(ticker, 200)
    df = df.set_index('date')
    cerebro = bt.Cerebro()
    cerebro.adddata(bt.feeds.PandasData(dataname=df))

    cerebro.addstrategy(Strategy)

    print('Starting portfolio value: %f' % cerebro.broker.getvalue())
    cerebro.run()

    print('Final portfolio value: %f' % cerebro.broker.getvalue())