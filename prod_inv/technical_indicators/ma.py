import pandas as pd
import talib as tb
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker


def calculate_ma(length, period, date_reference, coins=None, _type='SMA'):
    if not coins:
        coins = all_tickers
    for c in coins:
        closes = db.session.query(Ticker).\
            filter(and_(Ticker.date <= date_reference, Ticker.coin == c, Ticker.period == period)).\
            order_by(Ticker.date.desc()).limit(length).all()

        close = [v.close for v in closes][::-1]
        df = pd.DataFrame(close, columns=['close'])
        if _type == 'SMA':
            ma = tb.MA(df.close, timeperiod=length)

        elif _type == 'EMA':
            ma = tb.EMA(df.close, timeperiod=length)
        try:
            ma_value = TechnicalIndicator(date_reference, period, c, _type + str(length), ma.iloc[-1])
            db.session.add(ma_value)
            db.session.commit()
        except Exception:
            db.session.rollback()
            print('Already has value ' + _type + ' ' + str(date_reference) + ' ' + str(length) + ' ' + str(ma.iloc[-1]))