import pickle

import numpy as np
from sqlalchemy import and_

from prod_inv.app import db
from prod_inv.models.balance import Balance
from prod_inv.models.order_book import OrderBook

drop_columns = ['id', 'coin', 'date', 'period',
                'high', 'low', 'open', 'close', 'volume', 'quote_volume',
                'weightedAverage',
                'BBUpper', 'BBLower', 'BBMiddle',
                'EMA9', 'EMA12', 'EMA26', 'EMA50',
                'SMA9', 'SMA12', 'SMA26', 'SMA50',
                'target_log_return_1', 'target_log_return_2', 'target_log_return_3',
                'target_log_return_4', 'target_log_return_5', 'target_log_return_6'
               ]


def check_credit(coin='USDT'):
    balance_coin = 0
    balance = db.session.query(Balance). \
        filter(Balance.coin == coin).all()
    balance_coin = sum([b.value for b in balance])
    return balance_coin


def check_open_orders(coin, close, date):
    order_book = db.session.query(OrderBook). \
        filter(and_(OrderBook.coin == coin),
               OrderBook.status == 'open').all()

    for o in order_book:
        exit = np.log(close / o.quote)
        if (exit <= o.stop_loss) or (exit >= o.take_profit):
            try:
                db.session.query(OrderBook).filter(OrderBook.id == o.id).update({'status': 'close',
                                                                                 'exit': exit,
                                                                                 'exit_quote': close,
                                                                                 'date_exit': date})
                db.session.commit()

                balance_usdt = Balance(int(date), 'USDT', float(o.volume * close))
                db.session.add(balance_usdt)
                db.session.commit()

                balance_coin = Balance(date, coin, float(-o.volume))
                db.session.add(balance_coin)
                db.session.commit()
            except Exception:
                db.session.rollback()
                print('Error exiting order ' + str(date))
                return False


def predict_signal(df, coin, threshold=0.8):
    signal = 0
    usdt_balance = check_credit()
    status = 'denied' if usdt_balance <= 0 else 'open'
    import ipdb;ipdb.set_trace()
    try:
        filename = '/Users/macbookpro/Documents/prod_inv/' + coin + '_model.sav'
        model = pickle.load(open(filename, 'rb'))
        mask = (
            ((df['log_return'] >= model['take_profit'])
             | (df['log_return_2'] >= model['take_profit'])
             | (df['log_return_3'] >= model['take_profit'])
             | (df['log_return_4'] >= model['take_profit'])
             ))
        df.loc[mask, 'last_target'] = 1
        df.loc[~mask, 'last_target'] = 0
        X = df.drop(drop_columns).dropna()

    except Exception as e:
        print('No model found for ' + coin)
        return False

    X = model['Scaler'].transform(X.ravel().reshape(1, -1))
    predicted_proba = model['Model'].predict_proba(X)
    print('Predicted prob: ' + str(predicted_proba))
    if predicted_proba[0][1] >= threshold:
        signal = 1

    if signal:
        quote = df.close
        volume = (max((usdt_balance/4), 25) / quote)
        take_profit = model['take_profit']
        stop_loss = model['stop_loss']
        date = df.date
        try:
            order_book = OrderBook(coin, int(date), float(quote), float(volume), float(stop_loss), float(take_profit)
                                   , status, None, None, None)
            db.session.add(order_book)
            db.session.commit()

        except Exception:
            db.session.rollback()
            print('Error sending order ' + str(date))
            return False


        if usdt_balance > 0:
            try:
                balance_usdt = Balance(int(date), 'USDT', -float(max((usdt_balance/4), 25) ))
                db.session.add(balance_usdt)
                db.session.commit()

                balance_coin = Balance(int(date), coin, float(volume))
                db.session.add(balance_coin)
                db.session.commit()

            except Exception:
                db.session.rollback()
                print('Error sending order: not enough money ' + str(date))
                return False
    return True
