"""Test the migrate command."""

import pytest
from pathlib import Path
import tempfile
import os

from fitler.core import db
from fitler.commands import migrate
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync


def test_migrate_creates_tables(tmp_path):
    """Test that migrate creates all required tables."""
    # Set up a temporary database
    db_path = tmp_path / "test.db"
    original_db_path = db.database
    db.init(str(db_path))

    try:
        # Run migrations
        migrate.run()

        # Verify tables exist by trying to use them
        # This will raise exceptions if tables don't exist
        Activity.select().count()
        ProviderSync.select().count()

        # Try creating records to verify table structure
        test_sync = ProviderSync.create(year_month="2023-01", provider="strava")
        assert test_sync.year_month == "2023-01"
        assert test_sync.provider == "strava"

        test_activity = Activity.create(name="Test Activity")
        assert test_activity.name == "Test Activity"

    finally:
        # Clean up
        db.init(original_db_path)  # Restore original database path
        if db_path.exists():
            db_path.unlink()
