import backtrader as bt 
from fastquant.strategies.base import BaseStrategy


class SMACADXStrategy(BaseStrategy):
	"""
	Simple moving average crossover with ADX as opening signals 
	"""
	params = (
	("fast_period":4),
	("slow_period":9),
	)
	def __init__(self):
		super().init()
		self.fast_period=self.params.fast_period
		self.slow_period=self.params.slow_period
		sma_fast = bt.ind.SMA(period=self.fast_period)
		sma_slow = bt.ind.SMA(period=self.slow_period)
		adx = bt.ind.ADX()
		for value in adx:
			print(value)
		self.crossover = bt.ind.CrossOver(
			sma_fast, sma_slow)

	def buy_signal(self):
		return self.crossover > 0 and self.adx[0] >30

	def sell_signal(self):
		return self.crossover < 0