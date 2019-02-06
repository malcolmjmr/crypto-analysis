import os
import sys
from datetime import datetime as dt, timedelta as td
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
#from app import cache

DATA_DIR = 'tmp'

def breaches_and_retests(base, periods, prices_used=['close'], breach_delay=False):
    """ Determine when support and resistance are breached and retested

    """
    price_min = prices_used[0]
    price_max = prices_used[-1]
    breach_delay = breach_delay if breach_delay else td(seconds=0)
    rel_periods = periods[base.name+breach_delay:]
    
    if base.is_support:
        breached = rel_periods[rel_periods[price_max] < base[price_min]].index.min()
        retested = rel_periods[breached:][rel_periods[breached:][price_max] > base[price_min]].index.min()
    elif base.is_resistance:
        breached = rel_periods[rel_periods[price_min] > base[price_max]].index.min()
        retested = rel_periods[breached:][rel_periods[breached:][price_min] < base[price_max]].index.min()
        
    retested = pd.tslib.NaT if isinstance(breached, pd.tslib.NaTType) else retested
    
    if not isinstance(retested, pd.tslib.NaTType):
        breach_period = rel_periods[breached:retested]
        extrema_value = breach_period[price_min].min() if base.is_support else breach_period[price_min].max()
        reached_extrema = breach_period[extrema_value==breach_period[price_min]].index[0]
        
    else:
        reached_extrema = pd.NaT
        extrema_value = None
      
    return breached, retested, reached_extrema, extrema_value   

#@cache.memoize(timeout=60)
def get_bases(prices, prices_used=['close'], lookback_length=False, min_strength=0, print_summary=False, from_file=False, save=False, breach_delay=1):

    filename = '{}/{}_{}{}_BASES.csv'.format(DATA_DIR, prices.asset.values[0], prices.index.freq.n, prices.index.freq.name)

    print('getting base info {}'.format(filename), file=sys.stderr)
    if from_file and os.path.exists(filename):
        bases = pd.read_csv(filename, index_col='time')
        bases.index = pd.to_datetime(bases.index)
        for col in bases.dtypes[bases.dtypes=='object'].index.tolist():
            try:
                bases[col] = pd.to_datetime(bases[col])
            except:
                try:
                    bases[col] = pd.to_timedelta(bases[col])
                except:
                    pass
        return bases[prices.index.min():prices.index.max()]

    # take rolling average to smooth out time series and reduce number of bases 
    prices = prices.copy()

    prices[prices_used] = prices[prices_used].rolling(lookback_length).mean() if lookback_length else prices[prices_used]

    # find support and resistance 
    is_support = argrelextrema(prices[prices_used[0]].values, np.less)[0]
    is_resistance = argrelextrema(prices[prices_used[-1]].values, np.greater)[0]
    prices['is_support'] = prices.reset_index().reset_index()['index'].isin(is_support).tolist()
    prices['is_resistance'] = prices.reset_index().reset_index()['index'].isin(is_resistance).tolist()

    bases = prices[prices.is_support|prices.is_resistance].dropna().sort_index() 
    bases['price_level'] = bases.apply(lambda b: b[prices_used[0]] if b.is_support else b[prices_used[-1]], axis=1)
    #bases['last_price_level'] = bases.price_level.shift(1).values
    bases['strength_of_reversal'] = bases[((bases.is_support*1).diff()!=0)].price_level.pct_change().shift(-1).abs()
    bases['strength_of_prev_trend'] = bases.strength_of_reversal.shift()
    bases['prev_trend_start'] = bases.reset_index().time.shift().values
    bases['reversal_end'] = bases.reset_index().time.shift(-1).values
    bases['breached'], bases['retested'], bases['breach_extrema_reached'], bases['breach_extrema_value'] = zip(*bases.apply(breaches_and_retests, args=(prices, prices_used, breach_delay, ), axis=1))
    bases['time_prev_trend_to_created'] = bases.index - bases.prev_trend_start
    bases['time_created_to_end'] = bases.reversal_end - bases.index
    bases['time_created_to_breached'] = bases.breached - bases.index
    bases['time_breached_to_retested'] = bases.retested - bases.breached
    bases['time_breached_to_extrema'] = bases.breach_extrema_reached - bases.breached
    bases['pct_breach'] = (bases.price_level - bases.breach_extrema_value) / bases.price_level
    bases['pct_rebound'] = (bases.price_level.shift(-1) - bases.breach_extrema_value)/ bases.breach_extrema_value
    bases['pct_of_breach_retraced'] = (bases.price_level - bases.breach_extrema_value)/(bases.price_level.shift(-1) - bases.breach_extrema_value)
    bases['significance'] = (bases.strength_of_prev_trend.rank(pct=True) + (2*bases.strength_of_reversal.rank(pct=True)))/3
    bases['max_profit'] = (bases.price_level - bases.breach_extrema_value)/bases.breach_extrema_value
    bases['price_level_following_breach'] = bases.apply(lambda b: bases[b.breached:].head(1).price_level[0] if (not isinstance(b.breached, pd.tslib.NaTType) and not bases[b.breached:].empty) else None, axis=1)

    
    if print_summary:
        print('Number of bases: {}'.format(bases.shape[0]))
        base_freq = bases.shape[0]/prices.shape[0]
        print('Pct of bases: {}'.format(base_freq))
        breached_bases = bases[~bases.breached.isna()]
        retested_bases = breached_bases[~breached_bases.retested.isna()]
        breach_freq = breached_bases.shape[0]/bases.shape[0]
        retest_freq = retested_bases.shape[0]/breached_bases.shape[0]
        print('Percentage of breached bases: {}'.format(breach_freq))
        print('Percentage of retested bases: {}'.format(retest_freq))
        print('Joint frequency: {}'.format(base_freq*breach_freq*retest_freq))

    if save:
        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR)
        
        bases.to_csv(filename)
    
    columns = [
        'asset',
        'price_level',
        'is_support',
        'prev_trend_start',
        'reversal_end',
        'strength_of_reversal',
        'strength_of_prev_trend',
        'time_prev_trend_to_created',
        'time_created_to_end',
        'breached',
        'time_created_to_breached',
        'time_breached_to_extrema',
        'breach_extrema_reached',
        'breach_extrema_value',
        'time_breached_to_retested',
        'retested',
        'pct_breach',
        'pct_rebound',
        'pct_of_breach_retraced',
    ]
    
    return bases[columns]