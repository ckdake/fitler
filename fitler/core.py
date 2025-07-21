"""Core Fitler functionality and provider management."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Type
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import dateparser
from peewee import Model, fn

from .providers.spreadsheet import SpreadsheetActivities
from .providers.strava import StravaActivities
from .providers.ridewithgps import RideWithGPSActivities
from .providers.base import Activity
from .metadata import ActivityMetadata
from .provider_sync import ProviderSync
from .database import db

CONFIG_PATH = Path("fitler_config.json")

class Fitler:
    """Main Fitler class that handles configuration and provider management."""
    
    def __init__(self):
        # Load config first
        self.config = self._load_config()
        self.home_tz = ZoneInfo(self.config.get('home_timezone', 'US/Eastern'))
        
        # Initialize database
        db.connect(reuse_if_open=True)
        
        # Initialize providers
        self._spreadsheet = None
        self._strava = None
        self._ridewithgps = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from fitler_config.json."""
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        
        if "debug" not in config:
            config["debug"] = False
        if "provider_priority" not in config:
            config["provider_priority"] = "spreadsheet,ridewithgps,strava"
            
        return config
    
    @property
    def spreadsheet(self) -> Optional[SpreadsheetActivities]:
        """Get the spreadsheet provider, initializing it if needed."""
        if not self._spreadsheet and self.config.get("spreadsheet_path"):
            self._spreadsheet = SpreadsheetActivities(self.config["spreadsheet_path"])
        return self._spreadsheet
    
    @property
    def strava(self) -> Optional[StravaActivities]:
        """Get the Strava provider, initializing it if needed."""
        if not self._strava:
            token = os.environ.get("STRAVA_ACCESS_TOKEN")
            if token:
                self._strava = StravaActivities(
                    token,
                    refresh_token=os.environ.get("STRAVA_REFRESH_TOKEN"),
                    client_id=os.environ.get("STRAVA_CLIENT_ID"),
                    client_secret=os.environ.get("STRAVA_CLIENT_SECRET"),
                    token_expires=os.environ.get("STRAVA_TOKEN_EXPIRES")
                )
        return self._strava
    
    @property
    def ridewithgps(self) -> Optional[RideWithGPSActivities]:
        """Get the RideWithGPS provider, initializing it if needed."""
        if not self._ridewithgps:
            if all(os.environ.get(env) for env in ["RIDEWITHGPS_EMAIL", "RIDEWITHGPS_PASSWORD", "RIDEWITHGPS_KEY"]):
                self._ridewithgps = RideWithGPSActivities()
        return self._ridewithgps
    
    @property
    def enabled_providers(self) -> List[str]:
        """Get list of enabled providers."""
        providers = []
        if self.spreadsheet:
            providers.append('spreadsheet')
        if self.strava:
            providers.append('strava')
        if self.ridewithgps:
            providers.append('ridewithgps')
        return providers
        
    def fetch_activities_for_month(self, year_month: str) -> Dict[str, list]:
        """Fetch activities from all configured providers for the given month."""
        activities = {
            'spreadsheet': [],
            'strava': [],
            'ridewithgps': []
        }
        
        if self.spreadsheet:
            activities['spreadsheet'] = self.spreadsheet.fetch_activities_for_month(year_month)
        
        if self.strava:
            activities['strava'] = self.strava.fetch_activities_for_month(year_month)
        
        if self.ridewithgps:
            try:
                activities['ridewithgps'] = self.ridewithgps.fetch_activities_for_month(year_month)
            except Exception as e:
                print(f"\nRideWithGPS: Error fetching activities: {e}")
        
        return activities
    
    def provider_sync(self, year_month: str) -> Dict[str, list]:
        """Sync activities from all enabled providers for the given month.
        
        If any provider needs syncing, fetches fresh data and updates the database.
        Otherwise, returns cached data from the database.
        
        Returns a consistent format regardless of source (fresh or cached).
        """
        need_fetch = False
        for provider in self.enabled_providers:
            synced = ProviderSync.get_or_none(
                year_month=year_month,
                provider=provider
            )
            
            if not synced:
                need_fetch = True
                break
                
        if need_fetch:
            # Only fetch once if any provider needs syncing
            print(f"\nFetching fresh data for {year_month}")
            activities = self.fetch_activities_for_month(year_month)
            
            # Mark all providers as synced
            for provider in self.enabled_providers:
                ProviderSync.get_or_create(
                    year_month=year_month,
                    provider=provider
                )
        else:
            print(f"\nAll providers already synced for {year_month}, using cached data")
            activities = self._load_activities_from_db(year_month)
                
        return activities

    def _process_activity(self, act, provider: str) -> Dict[str, Any]:
        ts = int(getattr(act, 'departed_at', 0) or 0)
        provider_id = getattr(act, f'{provider}_id', None)
        
        metadata = None
        lookup_id = getattr(act, 'spreadsheet_id', None) if provider == 'spreadsheet' else provider_id
        
        if lookup_id:
            try:
                metadata = ActivityMetadata.select().where(getattr(ActivityMetadata, f'{provider}_id') == lookup_id).first()
            except Exception:
                pass
        
        if not metadata:
            metadata = ActivityMetadata()
            if ts:
                dt = datetime.fromtimestamp(ts, timezone.utc)
                eastern = dt.astimezone(self.home_tz)
                metadata.start_time = eastern
                metadata.date = eastern.date()
            metadata.save()
            
        act_data = {
            'id': provider_id if provider != 'spreadsheet' else getattr(act, 'spreadsheet_id', None),
            'name': getattr(act, 'name', getattr(act, 'notes', '')),
            'notes': getattr(act, 'notes', ''),
            'equipment': getattr(act, 'equipment', ''),
            'distance': getattr(act, 'distance', 0),
            'activity_type': getattr(act, 'activity_type', ''),
            'start_time': datetime.fromtimestamp(ts, timezone.utc) if ts else None
        }
        
        if provider_id:
            setattr(metadata, f'{provider}_id', provider_id)
            metadata.save()
        
        metadata.update_from_provider(provider, act_data, self.config)
        
        return {
            'provider': provider,
            'id': provider_id,
            'timestamp': ts,
            'distance': getattr(act, 'distance', 0),
            'obj': act,
            'metadata': metadata
        }

    def _load_activities_from_db(self, year_month: str) -> Dict[str, list]:
        """Load activities for all providers from the database for a given month."""
        query = ActivityMetadata.select().where(
            fn.strftime('%Y-%m', ActivityMetadata.start_time) == year_month
        )
        
        activities = {
            'spreadsheet': [],
            'strava': [],
            'ridewithgps': []
        }
        
        for metadata in query:
            # Parse start time for this activity
            start_dt = dateparser.parse(str(metadata.start_time)) if metadata.start_time else None
            
            # Create base activity kwargs with common fields
            base_kwargs = {
                'departed_at': str(int(start_dt.timestamp())) if start_dt else None,
                'distance': metadata.distance or 0,
                'activity_type': metadata.activity_type or '',
            }
            
            # Add all existing provider IDs to base kwargs
            for pid in ['strava_id', 'ridewithgps_id', 'spreadsheet_id']:
                if pid_value := getattr(metadata, pid, None):
                    base_kwargs[pid] = pid_value
            
            # Process each provider's data
            for provider in ['spreadsheet', 'strava', 'ridewithgps']:
                provider_data = metadata.get_provider_data(provider)
                if provider_data:
                    # Create a copy of base kwargs for this provider
                    activity_kwargs = base_kwargs.copy()
                    # Add provider-specific data
                    activity_kwargs.update({
                        'name': provider_data.get('name', ''),
                        'notes': provider_data.get('notes', ''),
                        'equipment': provider_data.get('equipment', ''),
                    })
                    activities[provider].append(Activity(**activity_kwargs))
        
        return activities
    
    def cleanup(self):
        """Clean up resources, close connections etc."""
        if db.is_connection_usable():
            db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
