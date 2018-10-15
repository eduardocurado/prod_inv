from datetime import datetime, timedelta

import requests

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.ticker import Ticker

base_polo_url = 'https://poloniex.com/public?command='


def get_current_ticker_prices(period, tickers):
    polo_url = base_polo_url + 'returnChartData&currencyPair={}&start={}&end={}&period={}'
    end_date = datetime.now()  # up until today
    start_date = (end_date - timedelta(hours=period / 3600))
    if not tickers:
        tickers = all_tickers

    for polo_ticker in tickers:
        base_url = polo_url.format(polo_ticker, start_date.timestamp(), end_date.timestamp(), period)
        re = requests.get(base_url, headers={'accept': 'application/json'})
        if re.status_code != 200:
            return
        response_body = re.json()
        t_value = response_body[0]

        coin = polo_ticker
        high = t_value['high']
        low = t_value['low']
        close = t_value['close']
        open = t_value['open']
        volume = t_value['volume']
        quoteVolume = t_value['quoteVolume']
        weightedAverage = t_value['weightedAverage']
        time_ticker = t_value['date']
        if high == 0:
            return
        ticker_value = Ticker(time_ticker, period, coin, open, close, high, low, volume, quoteVolume,
                              weightedAverage)

        try:
            db.session.add(ticker_value)
            db.session.commit()
        except Exception:
            db.session.rollback()
            print('Already has value Ticker')
    return 'Success'


# Historical in Days
def get_historical_ticker_prices(period, tickers, historical):
    polo_url = base_polo_url + 'returnChartData&currencyPair={}&start={}&end={}&period={}'
    end_date = datetime.now() + timedelta(hours=3) # up until today
    start_date = (end_date - timedelta(days=historical))
    if not tickers:
        tickers = all_tickers

    for polo_ticker in tickers:
        base_url = polo_url.format(polo_ticker, start_date.timestamp(), end_date.timestamp(), period)
        re = requests.get(base_url, headers={'accept': 'application/json'})
        if re.status_code != 200:
            return
        response_body = re.json()
        for t_value in response_body:
            coin = polo_ticker
            high = t_value['high']
            low = t_value['low']
            close = t_value['close']
            open = t_value['open']
            volume = t_value['volume']
            quoteVolume = t_value['quoteVolume']
            weightedAverage = t_value['weightedAverage']
            time_ticker = t_value['date']
            if high == 0:
                return
            ticker_value = Ticker(time_ticker, period, coin, open, close, high, low, volume, quoteVolume,
                                  weightedAverage)
            try:
                db.session.add(ticker_value)
                db.session.commit()
            except Exception:
                db.session.rollback()
                print('Already has value Ticker')

    return 'Success'
