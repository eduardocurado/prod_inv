from sqlalchemy import Column, String, Integer, Float, UniqueConstraint

from prod_inv.app import db


# Create our database model


class GoogleTrends(db.Model):
    __tablename__ = "google_trends"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    value = Column(Float())
    date = Column(Integer(), nullable=False)
    __table_args__ = (UniqueConstraint('coin', 'date'),)

    def __init__(self, ticker_date, coin, value):
        self.date = ticker_date
        self.coin = coin
        self.value = value

    def __repr__(self):
        return '<id {}>'.format(self.id)
