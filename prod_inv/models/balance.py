from sqlalchemy import Column, String, Integer, Float

from prod_inv.app import db


# Create our database model

class Balance(db.Model):
    __tablename__ = "balance"
    id = Column(Integer, primary_key=True)
    coin = Column(String(120), nullable=False)
    date = Column(Integer(), nullable=False)
    value = Column(Float(), nullable=False)

    def __init__(self, date, coin, value):
        self.date = date
        self.coin = coin
        self.value = value


    def __repr__(self):
        return '<id {}>'.format(self.id)
