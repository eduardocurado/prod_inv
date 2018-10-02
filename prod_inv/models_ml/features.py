import math

import numpy as np
import pandas as pd
from scipy.stats import stats
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker
from prod_inv.models_ml.utils import query_to_dict


def get_lagged_values(num_lags, df, indicators):
    lags = list(range(1, num_lags))
    for ind in indicators:
        for i in lags:
            df[ind + '_lag' + str(i)] = df[ind].shift(i)

    return df

# win in # samples
def calculate_slopes(df, win, result_df, slope_label):
    closes = df[['date', 'close']]
    seq = np.arange(0, win)
    di = []
    for i in range(win, len(closes)):
        v_closes = closes.iloc[i-win:i]
        base_date = v_closes.iloc[-1:][['date']].values[0][0]
        slope, intercept, r_value, p_value, std_err = stats.linregress(seq, v_closes['close'].values)
        di.append({
            'base_date': base_date,
            'slope': slope
        })

    for index, row in result_df.iterrows():
        date = row['date']
        slopes = [d for d in di if d['base_date'] <= date]
        if slopes:
            result_df.loc[result_df.index==index, slope_label] = sorted(slopes, key=lambda x: x['base_date'], reverse=True)[0]['slope']
    return result_df


def calculate_second_order_indicators(df):
    df['BBand_height'] = df['BBUpper'] / df['BBLower']
    df['BBand_lower_height'] = df['BBLower'] / df['close']
    df['BBand_upper_height'] = df['BBUpper'] / df['close']

    df['EMA_height12'] = df['EMA12'] / df['close']
    df['EMA_height26'] = df['EMA26'] / df['close']

    df['SMA_height12'] = df['SMA12'] / df['close']
    df['SMA_height26'] = df['SMA26'] / df['close']

    df['close_open'] = df['open'] / df['close']
    df['close_low'] = df['low'] / df['close']
    df['close_high'] = df['high'] / df['close']

    df['log_trend'] = np.log(df['TREND_COIN'] / df['TREND_COIN'].shift(1))

    df['rate_slope'] = df.slope / df.slope_short

    df['high_low'] = df.high / df.low

    df['ema_height'] = df.EMA12 / df.SMA12

    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    df['log_return_2'] = np.log(df.close / df.close.shift(2))
    df['log_return_3'] = np.log(df.close / df.close.shift(3))
    df['log_return_4'] = np.log(df.close / df.close.shift(4))



    return df.copy()

# window in days
def calculate_statistical_indicators(window, period, df):
    df['coin'].unique()
    look_back_size = math.floor((3600 * 24 * window) / period)
    for index, row in df.iterrows():
        base_date = row['date']
        window_df = df.loc[df['date'] <= base_date]
        if window_df.empty or len(window_df) < look_back_size:
            continue
        log_returns = window_df[-look_back_size:]['log_return']
        mean = log_returns.mean()
        var = log_returns.var()
        stdev = log_returns.std()
        df.loc[df.index==index, 'mean_return'] = mean
        df.loc[df.index==index, 'variance'] = var
        df.loc[df.index==index, 'stdev'] = stdev

    return df.copy()


def features_extractor(date_reference, coin, period, long_period=86400):
    tickers = db.session.query(Ticker). \
        filter(and_(
                    Ticker.date >= date_reference - long_period * 40,
                    Ticker.coin == coin)). \
        order_by(Ticker.date.asc()).all()

    tas = db.session.query(TechnicalIndicator). \
        filter(and_(
                    TechnicalIndicator.date >= date_reference - long_period * 40,
                    TechnicalIndicator.coin == coin,
                    TechnicalIndicator.indicator != 'SMA100',
                    TechnicalIndicator.indicator != 'EMA100')). \
        order_by(TechnicalIndicator.date.asc()).all()

    # Put Ticks Into DF
    df_tickers = pd.DataFrame(query_to_dict(tickers)).set_index(['coin', 'date', 'period'])
    # Put Technical Indicators Into DF
    df_tas = pd.DataFrame(query_to_dict(tas)).drop('id', axis=1)
    df_tas = pd.pivot_table(df_tas, index=['coin', 'date', 'period'], columns='indicator', values='value').copy()
    # Join Ticks and TAs
    all_df = df_tickers.join(df_tas).reset_index().sort_values(['date'], ascending=True).copy()

    big_df = all_df.loc[(all_df['coin'] == coin) & (all_df['period'] == long_period)]

    filter_df = all_df.loc[(all_df['coin'] == coin) & (all_df['period'] == period)]

    filter_df = calculate_slopes(big_df, 30, filter_df, 'slope')
    filter_df = calculate_slopes(filter_df, 30, filter_df, 'slope_short')

    full_df = calculate_second_order_indicators(filter_df)
    full_df = calculate_statistical_indicators(2, period, full_df)

    features_df = full_df.dropna().copy()
    features_df['target_log_return_1'] = np.log(features_df.close.shift(-1) / features_df.close)
    features_df['target_log_return_2'] = np.log(features_df.close.shift(-2) / features_df.close)
    features_df['target_log_return_3'] = np.log(features_df.close.shift(-3) / features_df.close)
    features_df['target_log_return_4'] = np.log(features_df.close.shift(-4) / features_df.close)
    features_df['target_log_return_5'] = np.log(features_df.close.shift(-5) / features_df.close)
    features_df['target_log_return_6'] = np.log(features_df.close.shift(-6) / features_df.close)
    clean_df = features_df.dropna()

    return clean_df
