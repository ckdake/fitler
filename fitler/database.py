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


def get_all_models() -> List[Type[Model]]:
    """Get all models that should be created in the database."""
    from .activity import Activity
    from .provider_sync import ProviderSync
    from .providers.strava.strava_activity import StravaActivity
    from .providers.garmin.garmin_activity import GarminActivity
    from .providers.ridewithgps.ridewithgps_activity import RideWithGPSActivity
    from .providers.spreadsheet.spreadsheet_activity import SpreadsheetActivity

    return [
        Activity,
        ProviderSync,
        StravaActivity,
        GarminActivity,
        RideWithGPSActivity,
        SpreadsheetActivity,
    ]
