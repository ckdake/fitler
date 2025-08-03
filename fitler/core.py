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
from .providers.stravajson import StravaJsonProvider
from .providers.base_provider_activity import BaseProviderActivity
from .database import db, migrate_tables, get_all_models

CONFIG_PATH = Path("fitler_config.json")


class Fitler:
    """Main Fitler class that handles configuration and provider management."""

    def __init__(self):
        # Load config first
        self.config = self._load_config()
        self.home_tz = ZoneInfo(self.config.get("home_timezone", "US/Eastern"))

        # Initialize database
        db.connect(reuse_if_open=True)
        
        # Always migrate tables on startup
        migrate_tables(get_all_models())

        # Initialize providers
        self._spreadsheet = None
        self._strava = None
        self._ridewithgps = None
        self._garmin = None
        self._file = None
        self._stravajson = None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from fitler_config.json."""
        with open(CONFIG_PATH) as f:
            config = json.load(f)

        # Set defaults if not present
        if "debug" not in config:
            config["debug"] = False
        if "provider_priority" not in config:
            config["provider_priority"] = "spreadsheet,ridewithgps,strava,garmin"

        return config

    @property
    def spreadsheet(self) -> Optional[SpreadsheetProvider]:
        """Get the spreadsheet provider, initializing it if needed."""
        provider_config = self.config.get("providers", {}).get("spreadsheet", {})

        if not self._spreadsheet and provider_config.get("enabled", False):
            path = provider_config.get("path")
            if path:
                # Add home_timezone to provider config
                enhanced_config = provider_config.copy()
                enhanced_config["home_timezone"] = self.config.get(
                    "home_timezone", "US/Eastern"
                )
                self._spreadsheet = SpreadsheetProvider(path, config=enhanced_config)
        return self._spreadsheet

    @property
    def strava(self) -> Optional[StravaProvider]:
        """Get the Strava provider, initializing it if needed."""
        provider_config = self.config.get("providers", {}).get("strava", {})

        if not self._strava and provider_config.get("enabled", False):
            token = os.environ.get("STRAVA_ACCESS_TOKEN")
            if token:
                # Add home_timezone to provider config
                enhanced_config = provider_config.copy()
                enhanced_config["home_timezone"] = self.config.get(
                    "home_timezone", "US/Eastern"
                )
                self._strava = StravaProvider(
                    token,
                    refresh_token=os.environ.get("STRAVA_REFRESH_TOKEN"),
                    token_expires=os.environ.get("STRAVA_TOKEN_EXPIRES"),
                    config=enhanced_config,
                )
        return self._strava

    @property
    def ridewithgps(self) -> Optional[RideWithGPSProvider]:
        """Get the RideWithGPS provider, initializing it if needed."""
        provider_config = self.config.get("providers", {}).get("ridewithgps", {})

        if not self._ridewithgps and provider_config.get("enabled", False):
            if all(
                os.environ.get(env)
                for env in [
                    "RIDEWITHGPS_EMAIL",
                    "RIDEWITHGPS_PASSWORD",
                    "RIDEWITHGPS_KEY",
                ]
            ):
                # Add home_timezone to provider config
                enhanced_config = provider_config.copy()
                enhanced_config["home_timezone"] = self.config.get(
                    "home_timezone", "US/Eastern"
                )
                self._ridewithgps = RideWithGPSProvider(config=enhanced_config)
        return self._ridewithgps

    @property
    def garmin(self) -> Optional[GarminProvider]:
        """Get the Garmin provider, initializing it if needed."""
        provider_config = self.config.get("providers", {}).get("garmin", {})

        if not self._garmin and provider_config.get("enabled", False):
            if os.environ.get("GARMINTOKENS"):
                # Add home_timezone to provider config
                enhanced_config = provider_config.copy()
                enhanced_config["home_timezone"] = self.config.get(
                    "home_timezone", "US/Eastern"
                )
                self._garmin = GarminProvider(config=enhanced_config)
        return self._garmin

    @property
    def file(self) -> Optional[FileProvider]:
        """Get the File provider, initializing it if needed."""
        provider_config = self.config.get("providers", {}).get("file", {})

        if not self._file and provider_config.get("enabled", False):
            glob_pattern = provider_config.get("glob")
            if glob_pattern:
                # Add home_timezone to provider config
                enhanced_config = provider_config.copy()
                enhanced_config["home_timezone"] = self.config.get(
                    "home_timezone", "US/Eastern"
                )
                self._file = FileProvider(glob_pattern, config=enhanced_config)
        return self._file

    @property
    def stravajson(self) -> Optional[StravaJsonProvider]:
        """Get the StravaJSON provider, initializing it if needed."""
        provider_config = self.config.get("providers", {}).get("stravajson", {})

        if not self._stravajson and provider_config.get("enabled", False):
            folder = provider_config.get("folder")
            if folder:
                # Add home_timezone to provider config
                enhanced_config = provider_config.copy()
                enhanced_config["home_timezone"] = self.config.get(
                    "home_timezone", "US/Eastern"
                )
                self._stravajson = StravaJsonProvider(folder, config=enhanced_config)
        return self._stravajson

    @property
    def enabled_providers(self) -> List[str]:
        """Get list of enabled providers based on config."""
        providers = []
        providers_config = self.config.get("providers", {})

        for provider_name in [
            "spreadsheet",
            "strava",
            "ridewithgps",
            "garmin",
            "file",
            "stravajson",
        ]:
            if providers_config.get(provider_name, {}).get("enabled", False):
                # Only add if required credentials/paths are available
                provider = getattr(self, provider_name)
                if provider:
                    providers.append(provider_name)

        return providers

    def pull_activities(self, year_month: str) -> Dict[str, List[BaseProviderActivity]]:
        """Pull activities from all enabled providers for the given month.

        This is the main entry point for fetching data from providers.
        Each provider handles its own API interaction and database updates.

        Returns:
            Dict mapping provider names to lists of BaseProviderActivity objects
        """
        activities = {}

        # Get the list of enabled providers from the config
        enabled_providers = self.enabled_providers

        # Pull from each enabled provider
        for provider_name in enabled_providers:
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
