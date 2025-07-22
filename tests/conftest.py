import pytest
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from fitler.database import migrate_tables

@pytest.fixture(scope="session", autouse=True)
def migrate_db():
    migrate_tables([Activity, ProviderSync])