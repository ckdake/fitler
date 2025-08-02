import os
import pytest
from peewee import SqliteDatabase

from fitler import db as db_module
from fitler.database import migrate_tables, get_all_models

def run_migrations():
        models = get_all_models()
        migrate_tables(models)

@pytest.fixture(scope="session", autouse=True)
def test_db():
    test_db_path = "test.sqlite3"
    test_db = SqliteDatabase(test_db_path)
    db_module.set_db(test_db)
    test_db.connect()
    run_migrations()
    yield
    test_db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
