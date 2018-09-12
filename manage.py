import os

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from prod_inv.app import app, db
from prod_inv.models.google_trends import GoogleTrends
from prod_inv.models.ticker import Ticker
from prod_inv.models.technical_indicator import TechnicalIndicator
from prod_inv.models.book import Book
from prod_inv.models.ml_model import MLModel
app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
    db.create_all()

