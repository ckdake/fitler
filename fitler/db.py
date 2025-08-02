from peewee import SqliteDatabase

db = SqliteDatabase("metadata.sqlite3")


def set_db(new_db):
    """Override db for testing"""
    global db
    db = new_db
