import math

import numpy as np
import pandas as pd

from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker
from prod_inv.models_ml.utils import query_to_dict, get_slope


def get_lagged_values(num_lags, df, indicators):
    lags = list(range(1, num_lags))
    for ind in indicators:
        for i in lags:
            df[ind + '_lag' + str(i)] = df[ind].shift(i)

    return df

def features_extractor(date_reference, date_base, coin, period, long_period=86400):
    tickers = db.session.query(Ticker). \
        filter(and_(Ticker.date >= date_base,
                    Ticker.date <= date_reference,
                    Ticker.coin == coin)). \
        order_by(Ticker.date.asc()).all()

    tas = db.session.query(TechnicalIndicator). \
        filter(and_(TechnicalIndicator.date >= date_base,
                    TechnicalIndicator.date <= date_reference,
                    TechnicalIndicator.coin == coin,
                    TechnicalIndicator.indicator != 'SMA100',
                    TechnicalIndicator.indicator != 'EMA100')). \
        order_by(TechnicalIndicator.date.asc()).all()

    df_tickers = pd.DataFrame(query_to_dict(tickers)).set_index(['coin', 'date', 'period'])
    df_tas = pd.DataFrame(query_to_dict(tas)).drop('id', axis=1)
    df_tas = pd.pivot_table(df_tas, index=['coin', 'date', 'period'], columns='indicator', values='value').copy()
    all_df = df_tickers.join(df_tas).reset_index()

    big_df = all_df.loc[(all_df['period'] == long_period)].dropna()
    filter_df = all_df.loc[(all_df['period'] == period)].dropna()

    closes = big_df[['date', 'close']]
    di = get_slope(30, closes)

    for index, row in filter_df.iterrows():
        date = row['date']
        slopes = [d for d in di if d['base_date'] <= date]
        if slopes:
            filter_df.ix[index, 'slope'] = sorted(slopes, key=lambda x: x['base_date'], reverse=True)[0]['slope']

    closes = filter_df[['date', 'close']]
    di = get_slope(30, closes)
    for index, row in filter_df.iterrows():
        date = row['date']
        slopes = [d for d in di if d['base_date'] <= date]
        if slopes:
            filter_df.ix[index, 'slope_short'] = sorted(slopes, key=lambda x: x['base_date'], reverse=True)[0]['slope']

    filter_df['BBand_height'] = filter_df['BBUpper'] / filter_df['BBLower']
    filter_df['BBand_lower_height'] = filter_df['BBLower'] / filter_df['close']
    filter_df['BBand_upper_height'] = filter_df['BBUpper'] / filter_df['close']

    # filter_df['EMA_height9'] = filter_df['EMA9']/filter_df['close']
    filter_df['EMA_height12'] = filter_df['EMA12'] / filter_df['close']
    filter_df['EMA_height26'] = filter_df['EMA26'] / filter_df['close']
    # filter_df['EMA_height50'] = filter_df['EMA50']/filter_df['close']


    # filter_df['SMA_height9'] = filter_df['SMA9']/filter_df['close']
    filter_df['SMA_height12'] = filter_df['SMA12'] / filter_df['close']
    filter_df['SMA_height26'] = filter_df['SMA26'] / filter_df['close']
    # filter_df['SMA_height50'] = filter_df['SMA50']/filter_df['close']

    filter_df['close_open'] = filter_df['open'] / filter_df['close']
    filter_df['close_low'] = filter_df['low'] / filter_df['close']
    filter_df['close_high'] = filter_df['high'] / filter_df['close']

    filter_df['log_return'] = np.log(filter_df['close'] / filter_df['close'].shift(1))
    filter_df['log_return_2'] = np.log(filter_df.close / filter_df.close.shift(2))
    filter_df['log_return_3'] = np.log(filter_df.close / filter_df.close.shift(3))
    filter_df['log_return_4'] = np.log(filter_df.close / filter_df.close.shift(4))

    filter_df['coin'].unique()
    window = 2

    look_back_size = math.floor((3600 * 24 * window) / period)
    for index, row in filter_df.iterrows():
        base_date = row['date']
        window_df = filter_df.loc[filter_df['date'] <= base_date]
        if window_df.empty or len(window_df) < look_back_size:
            continue
        log_returns = window_df[-look_back_size:]['log_return']
        mean = log_returns.mean()
        var = log_returns.var()
        stdev = log_returns.std()
        filter_df.ix[index, 'mean_return'] = mean
        filter_df.ix[index, 'variance'] = var
        filter_df.ix[index, 'stdev'] = stdev

    drop_columns = ['coin', 'date', 'period',
                    'high', 'low', 'open', 'volume', 'quote_volume',
                    'weightedAverage',
                    'BBUpper', 'BBLower', 'BBMiddle',
                    'EMA9', 'EMA12', 'EMA26', 'EMA50',
                    'SMA9', 'SMA12', 'SMA26', 'SMA50',
                    'mean_return', 'variance', 'stdev',
                    ]

    indicators = [
        'ADX', 'ATR',
        'HISTOGRAM', 'MACD', 'MOMENTUM', 'RSI14', 'SIGNAL',
        'BBand_lower_height', 'BBand_upper_height',
        'slope_short',
        'EMA_height12', 'EMA_height26', 'SMA_height12', 'SMA_height26'
    ]

    clean_df = get_lagged_values(1, filter_df, indicators).drop(drop_columns, axis=1).dropna()

    return clean_df
