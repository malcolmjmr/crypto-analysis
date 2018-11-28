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
        
        csv_name = 'price_data/{}_{}_{}.csv'.format(self.name, base.upper(), quote.upper())
        
        if from_file:
            ohlcv = pd.read_csv(csv_name, parse_dates=['time'], infer_datetime_format=True, index_col='time')

        elif self.name == 'POLONIEX':
            market = '{}_{}'.format(quote.upper(), base.upper())
            response = poloniex_api('returnChartData', {
                    'currencyPair': market,
                    'start': to_unix_time(start),
                    'end': to_unix_time(end),
                    'period': interval_length.seconds
                })
            ohlcv = pd.DataFrame(response)
            ohlcv['time'] = pd.to_datetime(ohlcv['date'] * 1e9)
            ohlcv = ohlcv.set_index('time')
            ohlcv = ohlcv.rename(columns={'quoteVolume':'base_volume', 'volume': 'quote_volume'})
            
        if save:
            ohlcv.to_csv(csv_name)
            
        return ohlcv[['open','high','low','close','quote_volume','base_volume']]








####### Helpers #########

def to_unix_time(dt):
    """Convert datetime to unix time"""
    return int(time.mktime(dt.timetuple()))

def poloniex_api(command, args={}):
    url = 'https://poloniex.com/public?command='+command
    for arg, value in args.items():
        url += '&{}={}'.format(arg,value)
    return json.loads(requests.get(url).content.decode('utf-8'))
