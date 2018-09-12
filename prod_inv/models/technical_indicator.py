from sqlalchemy import Column, String, Integer, Float, UniqueConstraint

from prod_inv.app import db


# Create our database model


class TechnicalIndicator(db.Model):
    __tablename__ = "technical_indicator"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    value = Column(Float())
    indicator = Column(String(10))
    date = Column(Integer(), nullable=False)
    period = Column(Integer(), nullable=False)
    __table_args__ = (UniqueConstraint('coin', 'date', 'period', 'indicator'),)

    def __init__(self, ticker_date, period, coin, indicator, value):
        self.date = ticker_date
        self.period = period
        self.coin = coin
        self.indicator = indicator
        self.value = value

    def __repr__(self):
        return '<id {}>'.format(self.id)
