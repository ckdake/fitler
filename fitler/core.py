"""Core Fitler functionality and provider management."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo

from .providers.spreadsheet import SpreadsheetProvider
from .providers.strava import StravaProvider
from .providers.ridewithgps import RideWithGPSProvider
from .providers.garmin import GarminProvider
from .providers.file import FileProvider
from .activity import Activity
from .database import db

CONFIG_PATH = Path("fitler_config.json")


class Fitler:
    """Main Fitler class that handles configuration and provider management."""

    def __init__(self):
        # Load config first
        self.config = self._load_config()
        self.home_tz = ZoneInfo(self.config.get("home_timezone", "US/Eastern"))

        # Initialize database
        db.connect(reuse_if_open=True)

        # Initialize providers
        self._spreadsheet = None
        self._strava = None
        self._ridewithgps = None
        self._garmin = None
        self._file = None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from fitler_config.json."""
        with open(CONFIG_PATH) as f:
            config = json.load(f)

        if "debug" not in config:
            config["debug"] = False
        if "provider_priority" not in config:
            config["provider_priority"] = "spreadsheet,ridewithgps,strava,garmin"

        return config

    @property
    def spreadsheet(self) -> Optional[SpreadsheetProvider]:
        """Get the spreadsheet provider, initializing it if needed."""
        if not self._spreadsheet and self.config.get("spreadsheet_path"):
            self._spreadsheet = SpreadsheetProvider(self.config["spreadsheet_path"])
        return self._spreadsheet

    @property
    def strava(self) -> Optional[StravaProvider]:
        """Get the Strava provider, initializing it if needed."""
        if not self._strava:
            token = os.environ.get("STRAVA_ACCESS_TOKEN")
            if token:
                self._strava = StravaProvider(
                    token,
                    refresh_token=os.environ.get("STRAVA_REFRESH_TOKEN"),
                    client_id=os.environ.get("STRAVA_CLIENT_ID"),
                    client_secret=os.environ.get("STRAVA_CLIENT_SECRET"),
                    token_expires=os.environ.get("STRAVA_TOKEN_EXPIRES"),
                )
        return self._strava

    @property
    def ridewithgps(self) -> Optional[RideWithGPSProvider]:
        """Get the RideWithGPS provider, initializing it if needed."""
        if not self._ridewithgps:
            if all(
                os.environ.get(env)
                for env in [
                    "RIDEWITHGPS_EMAIL",
                    "RIDEWITHGPS_PASSWORD",
                    "RIDEWITHGPS_KEY",
                ]
            ):
                self._ridewithgps = RideWithGPSProvider()
        return self._ridewithgps

    @property
    def garmin(self) -> Optional[GarminProvider]:
        """Get the Garmin provider, initializing it if needed."""
        if not self._garmin:
            if os.environ.get("GARMINTOKENS"):
                self._garmin = GarminProvider()
        return self._garmin

    @property  
    def file(self) -> Optional[FileProvider]:
        """Get the File provider, initializing it if needed."""
        if not self._file:
            activity_file_glob = self.config.get("activity_file_glob")
            if activity_file_glob:
                self._file = FileProvider(activity_file_glob)
        return self._file

    @property
    def enabled_providers(self) -> List[str]:
        """Get list of enabled providers."""
        providers = []
        if self.spreadsheet:
            providers.append("spreadsheet")
        if self.strava:
            providers.append("strava")
        if self.ridewithgps:
            providers.append("ridewithgps")
        if self.garmin:
            providers.append("garmin")
        if self.file:
            providers.append("file")
        return providers

    def pull_activities(self, year_month: str) -> Dict[str, List[Activity]]:
        """Pull activities from all enabled providers for the given month.

        This is the main entry point for fetching data from providers.
        Each provider handles its own API interaction and database updates.

        Returns:
            Dict mapping provider names to lists of Activity objects
        """
        activities = {}

        # Pull from each enabled provider
        for provider_name in self.enabled_providers:
            provider = getattr(self, provider_name)
            if provider:
                try:
                    provider_activities = provider.pull_activities(year_month)
                    activities[provider_name] = provider_activities
                    print(
                        f"Pulled {len(provider_activities)} activities from {provider_name}"
                    )
                except Exception as e:
                    print(f"Error pulling from {provider_name}: {e}")
                    activities[provider_name] = []
            else:
                activities[provider_name] = []

        return activities

    def cleanup(self):
        """Clean up resources, close connections etc."""
        if db.is_connection_usable():
            db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
