"""Core Fitler functionality and provider management."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from .providers.spreadsheet import SpreadsheetActivities
from .providers.strava import StravaActivities
from .providers.ridewithgps import RideWithGPSActivities
from .metadata import ActivityMetadata, db

CONFIG_PATH = Path("fitler_config.json")

class Fitler:
    """Main Fitler class that handles configuration and provider management."""
    
    def __init__(self):
        self.config = self._load_config()
        self.home_tz = ZoneInfo(self.config.get('home_timezone', 'US/Eastern'))
        
        # Initialize database
        db.connect()
        
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
    
    def cleanup(self):
        """Clean up resources, close connections etc."""
        if db.is_connection_usable():
            db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
