from peewee import SqliteDatabase

db = SqliteDatabase("metadata.sqlite3")

def set_db(new_db):
    """Set the global database instance, used to allow testing to use a real but separate database"""
    global db
    db = new_db
