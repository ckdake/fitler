"""Core Activity model for fitler."""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
import dateparser
import pytz

from peewee import (
    Model,
    DateTimeField,
    CharField,
    DecimalField,
    FloatField,
    IntegerField,
    DateField,
    TextField,
    SQL,
)

from fitler.database import db

from fitler.providers.strava.strava_activity import StravaActivity
from fitler.providers.garmin.garmin_activity import GarminActivity
from fitler.providers.ridewithgps.ridewithgps_activity import (
    RideWithGPSActivity,
)
from fitler.providers.spreadsheet.spreadsheet_activity import (
    SpreadsheetActivity,
)


class Activity(Model):
    """
    Central logical representation of an activity in fitler.

    This represents the "source of truth" activity that can be linked to
    multiple provider-specific activity records. Each Activity represents
    a single logical workout/ride/activity.
    """

    # Core activity data - the authoritative/computed values
    start_time = CharField(null=True, index=True)  # Stored as Unix timestamp string
    date = DateField(null=True, index=True)
    distance = FloatField(null=True)  # in miles

    # Authoritative names and descriptions
    name = CharField(null=True)  # The canonical name for the activity
    notes = TextField(null=True)  # Additional notes/description

    # Equipment and conditions (authoritative)
    equipment = CharField(null=True)
    activity_type = CharField(null=True)
    temperature = DecimalField(null=True)

    # Location data (authoritative)
    location_name = CharField(null=True)
    city = CharField(null=True)
    state = CharField(null=True)

    # Performance metrics (authoritative)
    duration_hms = CharField(null=True)
    max_speed = DecimalField(null=True)
    avg_heart_rate = IntegerField(null=True)
    max_heart_rate = IntegerField(null=True)
    calories = IntegerField(null=True)
    max_elevation = IntegerField(null=True)
    total_elevation_gain = IntegerField(null=True)
    avg_cadence = IntegerField(null=True)

    # Links to provider-specific activity records
    # These are the IDs from each provider for correlation
    spreadsheet_id = CharField(null=True, index=True)  # Row number or custom ID
    strava_id = CharField(null=True, index=True)
    garmin_id = CharField(null=True, index=True)
    ridewithgps_id = CharField(null=True, index=True)

    # Provider-specific data (stored as JSON) - kept for compatibility
    strava_data = TextField(null=True)  # JSON blob of raw Strava data
    ridewithgps_data = TextField(null=True)  # JSON blob of raw RWGPS data
    garmin_data = TextField(null=True)  # JSON blob of raw Garmin data
    spreadsheet_data = TextField(null=True)  # JSON blob of spreadsheet data

    # Metadata for correlation and tracking
    correlation_key = CharField(null=True, index=True)  # For deterministic matching
    last_updated = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    original_filename = CharField(null=True)  # For imported files
    source = CharField(default="fitler")  # Source of truth indicator

    # User association (for multi-user support in the future)
    user_id = CharField(null=True, index=True)

    class Meta:
        database = db
        indexes = (
            # Composite index for correlation key lookups
            (("correlation_key", "user_id"), False),
        )

    def set_start_time(self, datetimestring: str) -> None:
        """Set the start time from a string, converting to Unix timestamp."""
        if datetimestring:
            # If it's already a Unix timestamp, use it directly
            try:
                # Try to parse as Unix timestamp first
                timestamp = int(float(datetimestring))
                dt = datetime.fromtimestamp(timestamp, pytz.timezone("US/Eastern"))
                self.start_time = str(timestamp)
                self.date = dt.date()
                return
            except ValueError:
                pass

            # Parse as datetime string
            timezone_datetime_obj = dateparser.parse(
                datetimestring,
                settings={"TIMEZONE": "GMT", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            if timezone_datetime_obj:
                eastern = timezone_datetime_obj.astimezone(pytz.timezone("US/Eastern"))
                self.start_time = str(int(eastern.timestamp()))
                self.date = eastern.date()

    def update_from_provider(
        self, provider: str, data: dict, config: dict
    ) -> List[str]:
        """Update activity data from a provider, return list of changes made."""
        changes = []
        provider_priority = config.get(
            "provider_priority", "spreadsheet,ridewithgps,strava"
        ).split(",")

        # Prepare data for JSON storage by converting datetime objects
        serializable_data = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serializable_data[key] = value.isoformat()
            else:
                serializable_data[key] = value

        # Store the raw provider data
        setattr(self, f"{provider}_data", json.dumps(serializable_data))

        # Update provider ID if available
        provider_id = data.get("id")
        if provider_id:
            field_name = f"{provider}_id"
            try:
                current_id = getattr(self, field_name)
                if current_id != provider_id:
                    setattr(self, field_name, provider_id)
                    changes.append(f"Updated {provider} ID to {provider_id}")
            except AttributeError:
                setattr(self, field_name, provider_id)
                changes.append(f"Set {provider} ID to {provider_id}")

        # Update other provider IDs if available (e.g., spreadsheet has
        # strava_id, garmin_id, ridewithgps_id)
        for other_provider in ["strava", "garmin", "ridewithgps"]:
            other_id = data.get(f"{other_provider}_id")
            if other_id:
                field_name = f"{other_provider}_id"
                try:
                    current_id = getattr(self, field_name)
                    if current_id != other_id:
                        setattr(self, field_name, other_id)
                        changes.append(f"Updated {other_provider} ID to {other_id}")
                except AttributeError:
                    setattr(self, field_name, other_id)
                    changes.append(f"Set {other_provider} ID to {other_id}")

        # Only update other fields if this provider is authoritative
        current_auth = self.get_authoritative_provider(provider_priority)
        if provider == current_auth or not current_auth:
            # Core fields to check and update
            fields_to_update = {
                "name": data.get("name") or data.get("notes"),
                "equipment": data.get("equipment"),
                "distance": data.get("distance"),
                "activity_type": data.get("activity_type"),
                "start_time": data.get("start_time"),
                "source": data.get("source"),
            }

            for field, new_value in fields_to_update.items():
                if new_value and getattr(self, field) != new_value:
                    old_value = getattr(self, field)
                    setattr(self, field, new_value)
                    changes.append(
                        f"Updated {field} from '{old_value}' to '{new_value}'"
                    )

                    # If start_time was updated, also update the date field
                    if field == "start_time":
                        try:
                            timestamp = int(float(new_value))
                            dt = datetime.fromtimestamp(
                                timestamp, pytz.timezone("US/Eastern")
                            )
                            self.date = dt.date()
                        except (ValueError, TypeError):
                            pass

        if changes:
            self.last_updated = datetime.now()
            self.save()

        return changes

    def get_authoritative_provider(self, provider_priority: List[str]) -> Optional[str]:
        """Determine which provider should be considered authoritative for this activity."""
        for provider in provider_priority:
            if getattr(self, f"{provider}_id"):
                return provider
        return None

    def get_provider_data(self, provider: str) -> Optional[dict]:
        """Get the stored data for a specific provider."""
        data = getattr(self, f"{provider}_data")
        return json.loads(data) if data else None

    def get_needed_changes(self, config: dict) -> List[str]:
        """Get list of changes needed to synchronize across providers."""
        changes = []
        provider_priority = config.get(
            "provider_priority", "spreadsheet,ridewithgps,strava"
        ).split(",")
        auth_provider = self.get_authoritative_provider(provider_priority)

        if not auth_provider:
            return changes

        auth_data = self.get_provider_data(auth_provider)
        if not auth_data:
            return changes

        # Check each provider against the authoritative data
        for provider in provider_priority:
            if provider == auth_provider:
                continue

            provider_data = self.get_provider_data(provider)
            provider_id = getattr(self, f"{provider}_id")

            # If provider doesn't have this activity yet
            if not provider_id and provider == "spreadsheet":
                changes.append(
                    f"Create new entry in {provider} for "
                    f"'{auth_data.get('name', 'Untitled')}' starting at {self.start_time}"
                )
            elif provider_data:
                # Check for mismatches in key fields
                for field in ["name", "equipment"]:
                    auth_value = auth_data.get(field)
                    provider_value = provider_data.get(field)
                    if auth_value and provider_value and auth_value != provider_value:
                        changes.append(
                            f"Update {provider} {field} from '{provider_value}' to '{auth_value}'"
                        )

        return changes

    def to_json(self) -> str:
        """Convert activity metadata to JSON string."""
        data = {}
        # Manually list the fields to avoid peewee internals
        fields = [
            "start_time",
            "date",
            "distance",
            "name",
            "notes",
            "equipment",
            "activity_type",
            "temperature",
            "location_name",
            "city",
            "state",
            "duration_hms",
            "max_speed",
            "avg_heart_rate",
            "max_heart_rate",
            "calories",
            "max_elevation",
            "total_elevation_gain",
            "avg_cadence",
            "spreadsheet_id",
            "strava_id",
            "garmin_id",
            "ridewithgps_id",
            "strava_data",
            "ridewithgps_data",
            "garmin_data",
            "spreadsheet_data",
            "last_updated",
            "original_filename",
            "source",
        ]

        for field_name in fields:
            value = getattr(self, field_name, None)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            data[field_name] = value
        return json.dumps(data, sort_keys=True, indent=4)

    def to_dict(self):
        """Convert activity to dictionary."""
        return {
            "name": getattr(self, "name", None),
            "distance": getattr(self, "distance", None),
            "equipment": getattr(self, "equipment", None),
            "activity_type": getattr(self, "activity_type", None),
            "strava_id": getattr(self, "strava_id", None),
            "ridewithgps_id": getattr(self, "ridewithgps_id", None),
            "spreadsheet_id": getattr(self, "spreadsheet_id", None),
        }

    def generate_correlation_key(self) -> str:
        """Generate a correlation key for matching activities across providers.

        This should be deterministic and slightly fuzzy to account for different
        distance calculations across providers.
        """
        if not self.start_time or not self.distance:
            return ""

        try:
            # Convert timestamp to date string
            dt = datetime.fromtimestamp(int(self.start_time), pytz.UTC)
            date_str = dt.strftime("%Y-%m-%d")

            # Round distance to nearest 0.1 mile for fuzzy matching
            rounded_distance = round(float(self.distance) * 10) / 10

            return f"{date_str}_{rounded_distance}"
        except (ValueError, TypeError):
            return ""

    def update_correlation_key(self) -> None:
        """Update the correlation key based on current start_time and distance."""
        self.correlation_key = self.generate_correlation_key()

    def get_linked_provider_activities(self) -> Dict[str, Any]:
        """Get all linked provider-specific activity records.

        Returns a dict with provider names as keys and activity objects as values.
        """
        linked = {}

        # Check each provider
        if self.strava_id:
            try:
                linked["strava"] = StravaActivity.get(
                    StravaActivity.strava_id == self.strava_id
                )
            except StravaActivity.DoesNotExist:
                pass

        if self.garmin_id:
            try:
                linked["garmin"] = GarminActivity.get(
                    GarminActivity.garmin_id == self.garmin_id
                )
            except GarminActivity.DoesNotExist:
                pass

        if self.ridewithgps_id:
            try:
                linked["ridewithgps"] = RideWithGPSActivity.get(
                    RideWithGPSActivity.ridewithgps_id == self.ridewithgps_id
                )
            except RideWithGPSActivity.DoesNotExist:
                pass

        if self.spreadsheet_id:
            try:
                linked["spreadsheet"] = SpreadsheetActivity.get(
                    SpreadsheetActivity.spreadsheet_id == self.spreadsheet_id
                )
            except SpreadsheetActivity.DoesNotExist:
                pass

        return linked
