import os
import pytest
from peewee import SqliteDatabase
from fitler import db as db_module
from fitler.database import migrate_tables, get_all_models


@pytest.fixture(scope="session", autouse=True)
def test_db():
    test_db_path = "test.sqlite3"
    test_db = SqliteDatabase(test_db_path)
    db_module.set_db(test_db)
    # Rebind all models to the test DB
    for model in get_all_models():
        model._meta.set_database(test_db)
    test_db.connect()
    migrate_tables(get_all_models())
    yield
    test_db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
