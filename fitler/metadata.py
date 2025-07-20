"""Defines our data model for tracking activities across multiple providers."""

import json
import dateparser
import pytz
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from peewee import (
    SqliteDatabase,
    Model,
    DateTimeField,
    CharField,
    DecimalField,
    FloatField,
    IntegerField,
    DateField,
    TextField,
)

db = SqliteDatabase("metadata.sqlite3")

class ActivityMetadata(Model):
    # Core activity data
    start_time = DateTimeField(null=True, index=True)  # Stored in US/Eastern
    date = DateField(null=True, index=True)
    distance = FloatField(null=True)  # in miles
    
    # Names and descriptions
    name = CharField(null=True)  # The canonical name for the activity
    notes = TextField(null=True)  # Additional notes/description
    
    # Equipment and conditions
    equipment = CharField(null=True)
    activity_type = CharField(null=True)
    temperature = DecimalField(null=True)
    
    # Location data
    location_name = CharField(null=True)
    city = CharField(null=True)
    state = CharField(null=True)
    
    # Performance metrics
    duration_hms = CharField(null=True)
    max_speed = DecimalField(null=True)
    avg_heart_rate = IntegerField(null=True)
    max_heart_rate = IntegerField(null=True)
    calories = IntegerField(null=True)
    max_elevation = IntegerField(null=True)
    total_elevation_gain = IntegerField(null=True)
    avg_cadence = IntegerField(null=True)
    
    # Provider IDs and data
    spreadsheet_id = IntegerField(null=True, index=True)  # Row number in spreadsheet
    strava_id = IntegerField(null=True, index=True)
    garmin_id = IntegerField(null=True, index=True)
    ridewithgps_id = IntegerField(null=True, index=True)
    
    # Provider-specific data (stored as JSON)
    strava_data = TextField(null=True)  # JSON blob of raw Strava data
    ridewithgps_data = TextField(null=True)  # JSON blob of raw RWGPS data
    garmin_data = TextField(null=True)  # JSON blob of raw Garmin data
    spreadsheet_data = TextField(null=True)  # JSON blob of spreadsheet data
    
    # Tracking fields
    last_updated = DateTimeField(default=datetime.now)
    original_filename = CharField(null=True)  # For imported files
    source = CharField(null=True)  # Original data source

    class Meta:
        database = db

    def set_start_time(self, datetimestring: str) -> None:
        """Set the start time from a string, converting to US/Eastern."""
        if datetimestring:
            timezone_datetime_obj = dateparser.parse(
                datetimestring,
                settings={"TIMEZONE": "GMT", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            if timezone_datetime_obj:
                eastern = timezone_datetime_obj.astimezone(pytz.timezone("US/Eastern"))
                self.start_time = eastern.replace(microsecond=0)
                self.date = eastern.date()

    def update_from_provider(self, provider: str, data: dict, config: dict) -> List[str]:
        """Update activity data from a provider, return list of changes made."""
        changes = []
        provider_priority = config.get("provider_priority", "spreadsheet,ridewithgps,strava").split(",")
        
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
        provider_id = data.get('id')
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
        
        # Only update other fields if this provider is authoritative
        current_auth = self.get_authoritative_provider(provider_priority)
        if provider == current_auth or not current_auth:
            # Core fields to check and update
            fields_to_update = {
                'name': data.get('name') or data.get('notes'),
                'equipment': data.get('equipment'),
                'distance': data.get('distance'),
                'activity_type': data.get('activity_type'),
                'start_time': data.get('start_time'),
            }
            
            for field, new_value in fields_to_update.items():
                if new_value and getattr(self, field) != new_value:
                    old_value = getattr(self, field)
                    setattr(self, field, new_value)
                    changes.append(f"Updated {field} from '{old_value}' to '{new_value}'")
        
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
        provider_priority = config.get("provider_priority", "spreadsheet,ridewithgps,strava").split(",")
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
            if not provider_id and provider == 'spreadsheet':
                changes.append(f"Create new entry in {provider} for '{auth_data.get('name', 'Untitled')}' starting at {self.start_time}")
            elif provider_data:
                # Check for mismatches in key fields
                for field in ['name', 'equipment']:
                    auth_value = auth_data.get(field)
                    provider_value = provider_data.get(field)
                    if auth_value and provider_value and auth_value != provider_value:
                        changes.append(f"Update {provider} {field} from '{provider_value}' to '{auth_value}'")
        
        return changes

    def to_json(self) -> str:
        """Convert activity metadata to JSON string."""
        data = {}
        for field in self._meta.sorted_fields:  # Use sorted_fields instead of fields
            value = getattr(self, field.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            data[field.name] = value
        return json.dumps(data, sort_keys=True, indent=4)

    @classmethod
    def migrate(cls) -> None:
        """Create or update the database schema."""
        db.connect()
        db.create_tables([cls])
        db.close()
