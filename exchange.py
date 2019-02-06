import os
import numpy as np 
import scipy as sp 
import pandas as pd
import requests
import json
import time
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt 
import seaborn as sns
sns.set(rc={"figure.figsize": (20, 10)})  
from mpl_finance import candlestick_ohlc, volume_overlay3
import matplotlib.dates as mdates

#PRICE_COLS = ['open','high','low','close']
#VOLUME_COLS = ['quote_volume','base_volume']

DATA_DIR = 'tmp'

class Exchange:
    
    def __init__(self, name):
        self.name = name.upper()
        
    def get_tickers(limit=100):
        pass
    
    def get_gainers(self, limit=10):
        pass
    
    def get_losers(self, limit=10):
        pass
    
    def get_ohlcv(self, base, quote, 
                  start=datetime(2000,1,1), end=datetime.now(), 
                  interval_length=timedelta(minutes=15), 
                  from_file=False, save=False):
        
        """
        Todo
        - get freqstr and add to file name
        """
        
        # check existance of directory and file 
        csv_name = '{}/{}_{}_{}.csv'.format(DATA_DIR, self.name, base.upper(), quote.upper())
        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR)
        elif os.path.exists(csv_name):
            ohlcv = pd.read_csv(csv_name, parse_dates=['time'], infer_datetime_format=True, index_col='time')
        else:
            ohlcv = pd.DataFrame()
            

        if self.name == 'POLONIEX':

            start = to_unix_time(ohlcv.index.max()) if ohlcv.index.max() > start else to_unix_time(start)
            end = to_unix_time(end)
            market = '{}_{}'.format(quote.upper(), base.upper())
            response = poloniex_api('returnChartData', {
                    'currencyPair': market,
                    'start': start,
                    'end': end,
                    'period': interval_length.seconds
                })
            new_trades = pd.DataFrame(response)
            new_trades['time'] = pd.to_datetime(new_trades['date'] * 1e9)
            new_trades = new_trades.set_index('time')
            new_trades = new_trades.rename(columns={'quoteVolume':'base_volume', 'volume': 'quote_volume'})  
            if not ohlcv.empty and len(new_trades) > 1:
                ohlcv = pd.concat([ohlcv, new_trades])
            elif ohlcv.empty and len(new_trades) > 1:
                ohlcv = new_trades
            ohlcv['asset'] = base
        
        # save
        ohlcv.to_csv(csv_name)
            
        return ohlcv[['asset','open','high','low','close','quote_volume','base_volume']]



####### Helpers #########

def to_unix_time(dt):
    """Convert datetime to unix time"""
    return int(time.mktime(dt.timetuple()))

def poloniex_api(command, args={}):
    url = 'https://poloniex.com/public?command='+command
    for arg, value in args.items():
        url += '&{}={}'.format(arg,value)
    return json.loads(requests.get(url).content.decode('utf-8'))

def change_period_freq(df, period_freq):
    grouped = df.groupby(pd.Grouper(freq=period_freq))
    ohlc = pd.DataFrame({
        'asset': df[~df.asset.isna()].asset.values[0],
        'open': grouped.first().open,
        'high': grouped.high.max(),
        'low': grouped.low.min(),
        'close': grouped.last().close,
        'base_volume': grouped.base_volume.sum()
    }, index=grouped.count().index)
    ohlc.index.freq = period_freq
    return ohlc