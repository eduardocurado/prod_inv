from prod_inv.models.book import Book

from prod_inv.app import db


def set_signal(date_reference, coin, value, expected_value, stop_loss, target_profit, status):
    try:
        book_entity = Book(date_reference, coin, value, expected_value, stop_loss, target_profit, status)
        db.session.add(book_entity)
        db.session.commit()

    except Exception:
        db.session.rollback()
        print('Already has value Book ' + str(date_reference))