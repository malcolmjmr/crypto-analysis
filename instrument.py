import numpy as np 
import scipy as sp 
import pandas as pd
import requests
import json
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt 
import seaborn as sns
sns.set(rc={"figure.figsize": (20, 10)})  
from mpl_finance import candlestick_ohlc, volume_overlay3
import matplotlib.dates as mdates
from exchange import Exchange

PRICE_COLS = ['open','high','low','close']
VOLUME_COLS = ['quote_volume','base_volume']

class Instrument:
    
    def __init__(self, base, quote, exchange, block_size=1e4):
        self.base = base.upper()
        self.quote = quote.upper()
        self.exchange = Exchange(exchange.upper())
        self.name = '{}_{}_{}'.format(self.exchange.name, self.base, self.quote)
        self.block_size = block_size
        
    def get_history(self, start=datetime(2000,1,1), end=datetime.now(), interval_length=timedelta(minutes=15), refresh=False, from_file=True):
        if not hasattr(self, '_history') or refresh:
            self._history = self.exchange.get_ohlcv(self.base, self.quote, start=start, end=end, interval_length=interval_length, from_file=from_file)

        history = self._history[start:end]
        history[PRICE_COLS] = history[PRICE_COLS].groupby(pd.TimeGrouper(freq=interval_length)).mean()
        history[VOLUME_COLS] = history[VOLUME_COLS].groupby(pd.TimeGrouper(freq=interval_length)).sum()
        history = history.dropna(how='all')
        self._interval_length = interval_length
        
        return history
    
    def get_cost(self, period_length=timedelta(days=365)):
        pass
    
    def get_currency_volatility(self, lookback=7):
        self._history['curency_volatility'] = self.estimate_price_volatility(lookback=lookback)
        self._history.currency_volatility
    
    def get_value_volatility(self, lookback=7, account_currency='USD'):
        current_fx_rate = self.get_exchange_rate(account_currency=account_currency).loc[period.date()]
        return current_fx_rate * self.get_currency_volatility(lookback=lookback)
    
    def get_block_size(self):
        get
    
    def get_block_value(self, account_currency='USD'):
        pass
    
    def get_exchange_rates(self, refresh=False, account_currency='USD'):
        if not hasattr(self, '_fx_rate') or refresh:
            self._fx_rate = cryptocompare.get_daily_trades(self.quote, quote_currency=account_currency, from_file=True).open
            
        return self._fx_rate
    
    def get_SR(self):
        pass
    
    def estimate_price_volatility(self, lookback=7):
        return self.get_history(interval_length=self._interval_length).close.pct_change(lookback)
    
    def estimate_block_value(self):
        pass
    
    def plot_candles(self, start=datetime(2000,1,1), end=datetime.now(), interval_length=timedelta(minutes=15), show_volume=False, price_ax=None):
        price_ax = plt.subplot(2,1,1) if price_ax is None else price_ax
        ohlcv = self.get_history(start=start, end=end, interval_length=interval_length).reset_index()
        assert(ohlcv.shape[0] <= 1000), 'Too many candles to plot. Reduce timeframe.'
        ohlcv = ohlcv[['time', 'open', 'high', 'low', 'close', 'base_volume']]
        ohlcv['time'] = ohlcv['time'].map(mdates.date2num)
        bar_width = min(1/ohlcv.shape[0], .005)
        candlestick_ohlc(price_ax, ohlcv.values, width=bar_width, colorup='g', colordown='k',alpha=0.75)
        price_ax.xaxis_date()
        if show_volume:
            vol_ax = plt.subplot(4,1,3)
            ohlcv.set_index('time').base_volume.plot(ax=vol_ax)
            vol_ax.xaxis_date()
            
        return price_ax, ohlcv
            