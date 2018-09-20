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
    stop_loss= Column(Float(), nullable=False)
    target_profit = Column(Float(), nullable=False)
    status = Column(String(30), nullable=False)

    __table_args__ = (UniqueConstraint('coin', 'date'),)

    def __init__(self, ticker_date, coin, value, expected_value, stop_loss, target_profit, status):
        self.date = ticker_date
        self.coin = coin
        self.value = value
        self.expected_value = expected_value
        self.stop_loss = stop_loss
        self.target_profit = target_profit
        self.status = status

    def __repr__(self):
        return '<id {}>'.format(self.id)
