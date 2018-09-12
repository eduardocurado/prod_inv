import pandas as pd
import talib as tb
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker


def calculate_williams(period, date_reference, length, coins=None):
    if not coins:
        coins = all_tickers
    for c in coins:
        closes = db.session.query(Ticker). \
            filter(and_(Ticker.date <= date_reference, Ticker.coin == c, Ticker.period == period)). \
            order_by(Ticker.date.desc()).all()

        high = [v.high for v in closes][::-1]
        low = [v.low for v in closes][::-1]
        close = [v.close for v in closes][::-1]

        df = pd.DataFrame(columns=['close', 'high', 'low'])
        df['close'] = close
        df['high'] = high
        df['low'] = low

        willr = tb.WILLR(df.high, df.low, df.close, timeperiod=length)

        try:
            willr_entity = TechnicalIndicator(date_reference, period, c, 'WILLR',  willr.iloc[-1])
            db.session.add(willr_entity)
            db.session.commit()

        except Exception:
            db.session.rollback()
            print('Already has value WILLR ' + str(date_reference))
