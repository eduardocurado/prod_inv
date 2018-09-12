from sqlalchemy import Column, String, Integer, UniqueConstraint, Float

from prod_inv.app import db


# Create our database model


class Book(db.Model):
    __tablename__ = "book"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    date = Column(Integer(), nullable=False)
    value = Column(Float(), nullable=False)
    expected_value = Column(Float(), nullable=False)

    __table_args__ = (UniqueConstraint('coin', 'date'),)

    def __init__(self, ticker_date, coin, value, expected_value):
        self.date = ticker_date
        self.coin = coin
        self.value = value
        self.expected_value = expected_value

    def __repr__(self):
        return '<id {}>'.format(self.id)
