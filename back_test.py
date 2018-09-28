import math

import numpy as np
import pandas as pd
import pickle
from scipy import stats
from sqlalchemy import create_engine

pd.set_option('display.max_columns', 500)

engine = create_engine('postgresql+psycopg2://postgres@localhost/market')

def get_full_df():
    df = pd.read_sql_query('select * from "ticker" order by date',con=engine).drop('id', axis=1).set_index(['coin', 'date', 'period'])
    df_t = pd.read_sql_query('select * from "technical_indicator" order by date', con=engine).drop('id', axis=1)
    df_t = df_t.loc[(df_t['indicator'] != 'EMA100') & (df_t['indicator'] != 'SMA100')].copy()
    df_t = pd.pivot_table(df_t, index=['coin', 'date', 'period'], columns='indicator', values='value').copy()
    all_df = df.join(df_t).reset_index()
    return all_df.sort_values(['date'], ascending=True)


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

    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    df['log_return_2'] = np.log(df.close / df.close.shift(2))
    df['log_return_3'] = np.log(df.close / df.close.shift(3))
    df['log_return_4'] = np.log(df.close / df.close.shift(4))

    return df

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


def get_lag_indicators(df):
    lags = [1]
    indicators = [
        'ADX', 'ATR',
        'HISTOGRAM', 'MACD', 'MOMENTUM', 'RSI14', 'SIGNAL',
        'BBand_lower_height', 'BBand_upper_height',
        'slope_short',
        'EMA_height12', 'EMA_height26', 'SMA_height12', 'SMA_height26',
        'log_trend'
    ]
    for ind in indicators:
        for i in lags:
            df[ind + '_lag' + str(i)] = df[ind].shift(i)

    return df.copy()


def set_up_initial_data(coin):
    all_df = get_full_df()

    period = 86400
    big_df = all_df.loc[(all_df['coin'] == coin) & (all_df['period'] == period)]

    period = 14400
    filter_df = all_df.loc[(all_df['coin'] == coin) & (all_df['period'] == period)]
    filter_df = calculate_slopes(big_df, 30, filter_df, 'slope')
    filter_df = calculate_slopes(filter_df, 30, filter_df, 'slope_short')
    full_df = calculate_second_order_indicators(filter_df)
    full_df = calculate_statistical_indicators(2, period, full_df)

    return full_df


coins = ['USDT_BTC', 'USDT_ETH', 'USDT_LTC', 'USDT_XRP', 'USDT_ETC', 'USDT_DASH',
                'USDT_XMR',  'USDT_STR', 'USDT_EOS',]

for coin in coins:
    df = set_up_initial_data(coin)
    features_df = df.dropna().copy()
    features_df['target_log_return_1'] = np.log(features_df.close.shift(-1)/features_df.close)
    features_df['target_log_return_2'] = np.log(features_df.close.shift(-2)/features_df.close)
    features_df['target_log_return_3'] = np.log(features_df.close.shift(-3)/features_df.close)
    features_df['target_log_return_4'] = np.log(features_df.close.shift(-4)/features_df.close)
    features_df['target_log_return_5'] = np.log(features_df.close.shift(-5)/features_df.close)
    features_df['target_log_return_6'] = np.log(features_df.close.shift(-6)/features_df.close)

    filename = coin + 'back_test_sample.sav'
    pickle.dump(features_df.dropna(), open(filename, 'wb'))
