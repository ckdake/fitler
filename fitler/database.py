from typing import List, Type, cast
from peewee import Model

from .db import db
from .activity import Activity
from .provider_sync import ProviderSync
from .providers.base_provider_activity import BaseProviderActivity


def migrate_tables(models: List[Type[Model]]) -> None:
    db.connect(reuse_if_open=True)
    db.create_tables(models)
    db.close()


def get_all_models() -> List[Type[Model]]:
    return [Activity, ProviderSync] + list(
        cast(List[Type[Model]], BaseProviderActivity.__subclasses__())
    )
