"""Database configuration and initialization."""
from typing import List, Type
from peewee import Model, SqliteDatabase

# Initialize database
db = SqliteDatabase("metadata.sqlite3")

def migrate_tables(models: List[Type[Model]]) -> None:
    """Create or update database tables for the given models."""
    db.connect(reuse_if_open=True)
    db.create_tables(models)
    db.close()
