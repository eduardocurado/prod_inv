import pandas as pd
import talib as tb
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.ticker import Ticker


def calculate_macd(period, date_reference, length_short, length_long, length_macd, coins=None):
    if not coins:
        coins = all_tickers
    for c in coins:
        closes = db.session.query(Ticker). \
            filter(and_(Ticker.date <= date_reference, Ticker.coin == c, Ticker.period == period)). \
            order_by(Ticker.date.desc()).all()

        close = [v.close for v in closes][::-1]
        df = pd.DataFrame(close, columns=['close'])
        macd, macdsignal, macdhist = tb.MACD(df.close, fastperiod=length_short, slowperiod=length_long, signalperiod=length_macd)

        try:
            macd_line_entity = TechnicalIndicator(date_reference, period, c, 'MACD', macd.iloc[-1])
            db.session.add(macd_line_entity)

            signal_line_entity = TechnicalIndicator(date_reference, period, c, 'SIGNAL',  macdsignal.iloc[-1])
            db.session.add(signal_line_entity)

            histogram_entity = TechnicalIndicator(date_reference, period, c, 'HISTOGRAM',  macdhist.iloc[-1])
            db.session.add(histogram_entity)

            db.session.commit()

        except Exception:
            db.session.rollback()
            print('Already has value MACDS ' + str(date_reference))
