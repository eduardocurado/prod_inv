import pandas as pd
import talib as tb
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker


def calculate_boillinger_bands(length, period, date_reference, coins=None):
    if not coins:
        coins = all_tickers
    for c in coins:
        closes = db.session.query(Ticker).\
            filter(and_(Ticker.date <= date_reference, Ticker.coin == c, Ticker.period==period)).\
            order_by(Ticker.date.desc()).limit(length).all()

        close = [v.close for v in closes][::-1]
        df = pd.DataFrame(close, columns=['close'])
        upper, middle, lower = tb.BBANDS(df.close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)

        try:
            upper_band_value = TechnicalIndicator(date_reference, period, c, 'BBUpper', upper.iloc[-1])
            db.session.add(upper_band_value)
            lower_band_value = TechnicalIndicator(date_reference, period, c, 'BBLower', lower.iloc[-1])
            db.session.add(lower_band_value)
            middle_band_value = TechnicalIndicator(date_reference, period, c, 'BBMiddle', middle.iloc[-1])
            db.session.add(middle_band_value)
            db.session.commit()
        except Exception:
            db.session.rollback()
            print('Already has value BBands for: '  + str(date_reference) + ' ' + str(length) + ' ' + str(c))
