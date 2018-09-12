from sqlalchemy import Column, String, Integer, Float, UniqueConstraint

from prod_inv.app import db


# Create our database model


class Ticker(db.Model):
    __tablename__ = "ticker"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    high = Column(Float())
    low = Column(Float())
    close = Column(Float())
    open = Column(Float())
    volume = Column(Float())
    quote_volume = Column(Float())
    weightedAverage = Column(Float())
    date = Column(Integer(), nullable=False)
    period = Column(Integer(), nullable=False)
    __table_args__ = (UniqueConstraint('coin', 'date', 'period'),)

    def __init__(self, ticker_date, period, coin, open, close, high, low, volume, quote_volume,
								weightedAverage):
        self.date = ticker_date
        self.period = period
        self.coin = coin
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume
        self.quote_volume = quote_volume
        self.weightedAverage = weightedAverage

    def __repr__(self):
        return '<id {}>'.format(self.id)
