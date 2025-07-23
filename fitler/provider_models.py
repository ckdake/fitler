"""Provider-specific activity models for Fitler.

This module defines separate models for each provider's raw activity data,
keeping the source data separate from the logical Activity model.
"""

from peewee import (
    Model,
    CharField,
    DecimalField,
    IntegerField,
    DateTimeField,
    TextField,
    SQL,
)
from fitler.database import db


class BaseProviderActivity(Model):
    """Base class for provider-specific activity models."""

    # Core identification - this will be overridden in subclasses
    provider_id = CharField(max_length=50, index=True)
    name = CharField(max_length=255, null=True)
    distance = DecimalField(max_digits=10, decimal_places=6, null=True)
    start_time = CharField(max_length=20, null=True)  # Unix timestamp as string

    # Activity details
    activity_type = CharField(max_length=50, null=True)
    duration_hms = CharField(max_length=20, null=True)
    equipment = CharField(max_length=255, null=True)

    # Location
    location_name = CharField(max_length=255, null=True)
    city = CharField(max_length=100, null=True)
    state = CharField(max_length=50, null=True)

    # Performance metrics
    max_speed = DecimalField(max_digits=8, decimal_places=4, null=True)
    avg_heart_rate = IntegerField(null=True)
    max_heart_rate = IntegerField(null=True)
    calories = IntegerField(null=True)
    avg_cadence = IntegerField(null=True)

    # Elevation
    max_elevation = DecimalField(max_digits=10, decimal_places=4, null=True)
    total_elevation_gain = DecimalField(max_digits=10, decimal_places=4, null=True)

    # Environment
    temperature = DecimalField(max_digits=6, decimal_places=2, null=True)

    # Social
    with_names = CharField(max_length=255, null=True)

    # Notes
    notes = TextField(null=True)

    # Raw JSON data from provider (for future use)
    raw_data = TextField(null=True)

    # Timestamps
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = db
        abstract = True  # This is a base class


class StravaActivity(BaseProviderActivity):
    """Strava-specific activity data."""

    # Override provider_id with strava-specific field
    strava_id = CharField(max_length=50, unique=True, index=True)

    class Meta:
        database = db
        table_name = "strava_activities"


class GarminActivity(BaseProviderActivity):
    """Garmin-specific activity data."""

    # Override provider_id with garmin-specific field
    garmin_id = CharField(max_length=50, unique=True, index=True)

    class Meta:
        database = db
        table_name = "garmin_activities"


class RideWithGPSActivity(BaseProviderActivity):
    """RideWithGPS-specific activity data."""

    # Override provider_id with ridewithgps-specific field
    ridewithgps_id = CharField(max_length=50, unique=True, index=True)

    class Meta:
        database = db
        table_name = "ridewithgps_activities"


class SpreadsheetActivity(BaseProviderActivity):
    """Spreadsheet-specific activity data."""

    # For spreadsheet, we'll use row number or a generated ID
    spreadsheet_id = CharField(max_length=50, unique=True, index=True)

    # Spreadsheet-specific fields for tracking provider IDs
    stored_strava_id = CharField(max_length=50, null=True)
    stored_garmin_id = CharField(max_length=50, null=True)
    stored_ridewithgps_id = CharField(max_length=50, null=True)

    class Meta:
        database = db
        table_name = "spreadsheet_activities"


class FileActivity(BaseProviderActivity):
    """File-based activity data (.fit, .gpx, .tcx, etc.)."""

    # For files, use filename or path as ID
    file_id = CharField(max_length=255, unique=True, index=True)

    # File-specific fields
    file_path = CharField(max_length=500)
    file_type = CharField(max_length=10)  # fit, gpx, tcx, etc.
    file_size = IntegerField(null=True)
    file_modified = DateTimeField(null=True)

    class Meta:
        database = db
        table_name = "file_activities"
