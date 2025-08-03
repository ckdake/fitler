import os
import pytest
from peewee import SqliteDatabase
from fitler.db import configure_db, get_db
from fitler.database import migrate_tables, get_all_models


@pytest.fixture(scope="session", autouse=True)
def test_db():
    test_db_path = "test.sqlite3"
    configure_db(test_db_path)
    db = get_db()
    # Rebind all models to the test DB
    for model in get_all_models():
        model._meta.set_database(db)
    db.connect()
    migrate_tables(get_all_models())
    yield
    db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
