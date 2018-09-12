from sqlalchemy import Column, String, Integer, UniqueConstraint, Float

from prod_inv.app import db


# Create our database model


class MLModel(db.Model):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    name = Column(String(120), nullable=False)
    date = Column(Integer(), nullable=False)
    period = Column(Integer(), nullable=False)
    precision = Column(Float(), nullable=False)

    __table_args__ = (UniqueConstraint('coin', 'date', 'period'),)

    def __init__(self, ticker_date, period, coin, name, precision):
        self.date = ticker_date
        self.period = period
        self.coin = coin
        self.name = name
        self.precision = precision

    def __repr__(self):
        return '<id {}>'.format(self.id)
