import pytest
from fitler.metadata import ActivityMetadata

@pytest.fixture(scope="session", autouse=True)
def migrate_db():
    ActivityMetadata.migrate()