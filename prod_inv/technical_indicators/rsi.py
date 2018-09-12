import pandas as pd
import talib as tb
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker


def calculate_rsi(length, period, date_reference, coins=None):
    if not coins:
        coins = all_tickers
    for c in coins:
        values = db.session.query(Ticker). \
            filter(and_(Ticker.date <= date_reference, Ticker.coin == c, Ticker.period == period)). \
            order_by(Ticker.date.desc()).all()

        close = [v.close for v in values][::-1]
        df = pd.DataFrame(columns=['close'])
        df['close'] = close
        rsi_value = tb.RSI(df.close, timeperiod=14)
        try:
            rsi_entity = TechnicalIndicator(date_reference, period, c, 'RSI' + str(length), rsi_value.iloc[-1])
            db.session.add(rsi_entity)
            db.session.commit()
        except Exception:
            db.session.rollback()
            print('Already has value RSI ' + str(date_reference) + ' ' + c + ' ' + str(length) + ' ' + str(rsi_value.iloc[-1]))
