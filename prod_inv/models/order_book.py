import numpy as np
from sqlalchemy import Column, String, Integer, UniqueConstraint, Float

from prod_inv.app import db


# Create our database model

class OrderBook(db.Model):
    __tablename__ = "order_book"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    date = Column(Integer(), nullable=False)
    quote = Column(Float(), nullable=False)
    volume = Column(Float(), nullable=False)
    stop_loss= Column(Float(), nullable=False)
    take_profit = Column(Float(), nullable=False)
    status = Column(String(30), nullable=False)
    exit = Column(Float(), nullable=True)
    exit_quote = Column(Float(), nullable=True)
    date_exit = Column(Integer(), nullable=True)

    __table_args__ = (UniqueConstraint('coin', 'date'),)

    def __init__(self, coin, date , quote, volume, stop_loss, take_profit, status, _exit,
                 exit_quote, date_exit):
        self.coin = coin
        self.date = date
        self.quote = quote
        self.volume = volume
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.status = status
        self.exit = _exit
        self.exit_quote = exit_quote
        self.date_exit = date_exit


    def __repr__(self):
        return '<id {}>'.format(self.id)
