import numpy as np
from sqlalchemy import and_, or_

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.google_trends import GoogleTrends
from prod_inv.models.technical_indicator import TechnicalIndicator


def calculate_sum_google_trends(period, date_reference, length, coins=None):
    date_window = date_reference - period * length
    if not coins:
        coins = all_tickers
    for c in coins:
        google_trends = db.session.query(GoogleTrends). \
            filter(and_(GoogleTrends.date <= date_reference,
                        GoogleTrends.date > date_window,
                        or_(GoogleTrends.coin == c[5:], GoogleTrends.coin == 'crypto'))). \
            order_by(GoogleTrends.date.desc()).all()

        coin_trend = [v.value for v in google_trends if ('USDT_' + v.coin) == c][::-1]
        market_trend = [v.value for v in google_trends if v.coin == 'crypto'][::-1]
        try:
            trends_entity = TechnicalIndicator(date_reference, period, c, 'TREND_COIN',  np.sum(coin_trend) + np.sum(market_trend))
            db.session.add(trends_entity)
            db.session.commit()

        except Exception:
            db.session.rollback()
            print('Already has value GoogleTrends ' + str(date_reference))
