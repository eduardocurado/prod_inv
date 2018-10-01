import time
from datetime import datetime

from pytrends.request import TrendReq

from prod_inv.app import db
from prod_inv.fixtures import all_tickers
from prod_inv.models.google_trends import GoogleTrends


def get_trends(base_date, end_date):
    kw_list = ['crypto'] + [coin[5:] for coin in all_tickers]

    pytrends = TrendReq(hl='en-US', tz=360)

    date_window = datetime.fromtimestamp(base_date).isoformat()
    date_end = datetime.fromtimestamp(end_date).isoformat()
    i = 0

    while i <= len(all_tickers) + 1:
        trends = pytrends.get_historical_interest(kw_list[i:i + 4], year_start=int(date_window[:4]),
                                                  month_start=int(date_window[5:7]),
                                                  day_start=int(date_window[8:10]),
                                                  hour_start=int(date_window[11:13]),
                                                  year_end=int(date_end[:4]),
                                                  month_end=int(date_end[5:7]),
                                                  day_end=int(date_end[8:10]),
                                                  hour_end=int(date_end[11:13]),
                                                  cat=0, geo='', gprop='', sleep=60)

        if trends.empty:
            return 'Failed'


        trends = trends.drop(['isPartial'], axis=1).reset_index().drop_duplicates(subset=['date'],
                                                                                  keep="last").copy()

        columns_trends = trends.columns
        for index, row in trends.iterrows():
            for col in columns_trends:
                if col == 'date':
                    continue

                try:
                    google_entity = GoogleTrends(row['date'].timestamp(), col, row[col])
                    db.session.add(google_entity)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    print('Already has value ' + col + ' ' + str(row['date']))

        i += 4

    return 'Success'
