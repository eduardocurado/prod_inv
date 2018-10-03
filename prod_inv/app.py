import os
from datetime import datetime, timedelta

from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_

from prod_inv.fixtures import all_tickers

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

from prod_inv.collectors.poloniex import get_current_ticker_prices, get_historical_ticker_prices
from prod_inv.technical_indicators.calculate_indicators import calculate_indicators
from prod_inv.models.ticker import Ticker
from prod_inv.models_ml.features import features_extractor
from prod_inv.models_ml.prediction import predict_signal, check_open_orders
from prod_inv.collectors.google_trends import get_trends
from prod_inv.models_ml.select_model import train_model


@app.route('/get_historical_tickers', methods=['GET'])
def get_historical_ticker():
    period = int(request.args.get('period')) or 7200
    historical = int(request.args.get('historical')) or 30
    response_po = get_historical_ticker_prices(period, all_tickers, historical)
    if response_po == 'Success':
        return 'Insertion successfull'
    return 'Failed'


@app.route('/get_historical_google_trends', methods=['GET'])
def get_historical_trends():
    historical = int(request.args.get('historical')) or 30
    end_date = datetime.now()  # up until today
    start_date = (end_date - timedelta(days=historical))
    # start_date = start_date.replace(year=2018, day=10, month=9)
    # end_date.replace(year=2018, day=28, month=9)
    response_go = get_trends(start_date.timestamp(), end_date.timestamp())
    if response_go == 'Success':
        return 'Insertion successfull'
    return 'Failed'


@app.route('/get_historical_tas', methods=['GET'])
def get_historical_indicators():
    period = int(request.args.get('period')) or 14400
    historical = int(request.args.get('historical')) or 30
    end_date = datetime.now()  # up until today
    start_date = (end_date - timedelta(days=historical))

    for c in ['USDT_STR']:
        dates = db.session.query(Ticker).filter(and_(Ticker.coin == c, Ticker.period == period, Ticker.date >= start_date.timestamp())).order_by(Ticker.date.asc()).all()
        for d in dates:
            calculate_indicators(d, period, c)
    return 'Success'


@app.route('/get_google_trend', methods=['GET'])
def get_google_trend():
    period = int(request.args.get('period')) or 14400
    end_date = datetime.now()  # up until today
    start_date = (end_date - timedelta(seconds=period))
    response_go = get_trends(start_date.timestamp(), end_date.timestamp())
    if response_go == 'Success':
        return 'Insertion successfull'
    return 'Failed'


@app.route('/get_ticker', methods=['GET'])
def get_ticker():
    period = int(request.args.get('period')) or 14400
    response_po = get_current_ticker_prices(period, all_tickers)
    if response_po == 'Success':
        return 'Insertion successfull'
    return 'Failed'


@app.route('/get_tas', methods=['GET'])
def get_technical_indicators():
    period = int(request.args.get('period')) or 14400
    for c in all_tickers:
        dates = db.session.query(Ticker).filter(and_(Ticker.coin == c, Ticker.period == period)).order_by(Ticker.date.asc()).all()
        d = dates[-1]
        calculate_indicators(d, period, c)

    return 'Success'


@app.route('/train_models', methods=['GET'])
def train_models():
    period = request.args.get('period') or 14400
    training_period = request.args.get('historical') or None

    for c in all_tickers:
        dates = db.session.query(Ticker).filter(and_(Ticker.coin == c, Ticker.period == int(period))).order_by(Ticker.date.asc()).all()
        d = dates[-1]
        d_base = dates[0].date

        if training_period:
            d_base = d.date - int(training_period) * 86400

        features_df = features_extractor(d.date, d_base, c, int(period))
        # remove close when predicting
        train_model(features_df, c, d.date)

    return 'Success'


@app.route('/make_prediction', methods=['GET'])
def make_prediction():
    period = request.args.get('period') or 14400
    for c in all_tickers:
        dates = db.session.query(Ticker).filter(and_(Ticker.coin == c, Ticker.period == int(period))).order_by(Ticker.date.desc()).limit(1).all()
        d = dates[-1]
        value = d.close
        check_open_orders(c, value, d.date)
        features_df = features_extractor(d.date, c, int(period))
        predict_signal(features_df.iloc[-1], c, 0.5)


    return 'Success'


if __name__ == '__main__':
    app.run()
