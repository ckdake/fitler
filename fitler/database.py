"""Database configuration and initialization."""

from typing import List, Type, cast
from peewee import Model, SqliteDatabase

from .activity import Activity
from .provider_sync import ProviderSync
from .providers.base_activity import BaseProviderActivity

db = SqliteDatabase("metadata.sqlite3")

def migrate_tables(models: List[Type[Model]]) -> None:
    """Create or update database tables for the given models."""
    db.connect(reuse_if_open=True)
    db.create_tables(models)
    db.close()


def get_all_models() -> List[Type[Model]]:
    return [Activity, ProviderSync] + list(
        cast(List[Type[Model]], BaseProviderActivity.__subclasses__())
    )
