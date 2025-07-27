"""Strava provider for Fitler.

This module defines the StravaProvider class, which provides an interface
for interacting with Strava activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
import logging
from typing import List, Optional, Dict, Any
import dateparser
import datetime
import json
from pathlib import Path

from fitler.providers.base_provider import FitnessProvider
from fitler.providers.base_activity import BaseProviderActivity
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from fitler.providers.strava.strava_activity import StravaActivity
from peewee import DoesNotExist


class StravaProvider(FitnessProvider):
    def __init__(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_expires: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        
        # Initialize debug from environment and config
        self.debug = os.environ.get("STRAVALIB_DEBUG") == "1"
        if not self.debug and self.config:
            self.debug = self.config.get("debug", False)

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("stravalib").setLevel(logging.DEBUG)

        from stravalib import Client

        self.client = Client(access_token=token)
        if refresh_token:
            self.client.refresh_token = refresh_token
        if client_id:
            self.client._client_id = int(client_id)
        if client_secret:
            self.client._client_secret = client_secret
        if token_expires:
            self.client.token_expires = int(token_expires)

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "strava"

    def pull_activities(self, date_filter: Optional[str] = None) -> List[BaseProviderActivity]:
        """
        Pull activities from Strava API for the given date filter.
        If date_filter is None, pulls all activities (not implemented yet).
        Returns a list of StravaActivity objects.
        """
        # For now, require date_filter
        if date_filter is None:
            print("Strava provider: pulling all activities not implemented yet")
            return []
        
        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if existing_sync:
            print(f"Month {date_filter} already synced for {self.provider_name}")
            return []

        # Get raw activities from Strava API
        raw_activities = self._fetch_strava_activities_for_month(date_filter)
        print(f"Found {len(raw_activities)} Strava activities for {date_filter}")

        strava_activities = []
        for strava_lib_activity in raw_activities:
            try:
                # Convert stravalib activity to our StravaActivity
                strava_activity = self._convert_to_strava_activity(strava_lib_activity)
                
                # Check for duplicates
                existing = StravaActivity.get_or_none(
                    StravaActivity.strava_id == strava_activity.strava_id
                )
                if existing:
                    print(f"Skipping duplicate Strava activity {strava_activity.strava_id}")
                    continue
                
                # Save to database
                strava_activity.save()
                strava_activities.append(strava_activity)
                
            except Exception as e:
                print(f"Error processing Strava activity: {e}")
                continue

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)
        
        print(f"Synced {len(strava_activities)} Strava activities")
        return strava_activities

    def _fetch_strava_activities_for_month(self, year_month: str):
        """
        Return StravaActivity objects for the given year_month (YYYY-MM) using
        Stravalib API filters and pagination.
        """
        from dateutil.relativedelta import relativedelta
        import pytz

        year, month = map(int, year_month.split("-"))
        tz = pytz.UTC
        start_date = tz.localize(datetime.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)
        strava_activities = []
        
        # Use None for all optional params to ensure we get full activity details
        for strava_lib_activity in self.client.get_activities(
            after=start_date, before=end_date, limit=None
        ):
            try:
                # Create StravaActivity from stravalib Activity object
                strava_activity = StravaActivity()
                
                # Set basic activity data from Strava activity object
                strava_activity.strava_id = str(getattr(strava_lib_activity, "id", ""))
                strava_activity.name = str(getattr(strava_lib_activity, "name", "") or "")
                strava_activity.activity_type = str(getattr(strava_lib_activity, "type", "") or "")
                
                # Distance - convert from meters to miles
                distance_m = getattr(strava_lib_activity, "distance", None)
                if distance_m:
                    from decimal import Decimal
                    strava_activity.distance = Decimal(str(float(distance_m) * 0.000621371))
                
                # Start time as timestamp string
                start_date = getattr(strava_lib_activity, "start_date", None)
                if start_date:
                    strava_activity.start_time = str(int(start_date.timestamp()))
                
                # Duration
                elapsed_time = getattr(strava_lib_activity, "elapsed_time", None)
                if elapsed_time:
                    total_seconds = int(elapsed_time.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    strava_activity.duration_hms = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # Location data
                location_city = getattr(strava_lib_activity, "location_city", None)
                if location_city:
                    strava_activity.city = str(location_city)
                location_state = getattr(strava_lib_activity, "location_state", None)
                if location_state:
                    strava_activity.state = str(location_state)
                
                # Performance metrics
                max_speed = getattr(strava_lib_activity, "max_speed", None)
                if max_speed:
                    from decimal import Decimal
                    # Convert m/s to mph
                    strava_activity.max_speed = Decimal(str(float(max_speed) * 2.237))
                
                avg_hr = getattr(strava_lib_activity, "average_heartrate", None)
                if avg_hr:
                    strava_activity.avg_heart_rate = int(avg_hr)
                    
                max_hr = getattr(strava_lib_activity, "max_heartrate", None)
                if max_hr:
                    strava_activity.max_heart_rate = int(max_hr)
                
                kilojoules = getattr(strava_lib_activity, "kilojoules", None)
                if kilojoules:
                    strava_activity.calories = int(float(kilojoules) * 0.239)  # Convert kJ to calories
                
                # Elevation data
                elev_gain = getattr(strava_lib_activity, "total_elevation_gain", None)
                if elev_gain:
                    from decimal import Decimal
                    # Convert meters to feet
                    strava_activity.total_elevation_gain = Decimal(str(float(elev_gain) * 3.281))
                
                # Create raw data dict for storage
                raw_data = {
                    "id": getattr(strava_lib_activity, "id", None),
                    "name": getattr(strava_lib_activity, "name", None),
                    "type": getattr(strava_lib_activity, "type", None),
                    "distance": float(getattr(strava_lib_activity, "distance", 0) or 0),
                    "start_date": str(getattr(strava_lib_activity, "start_date", "")),
                    "elapsed_time": str(getattr(strava_lib_activity, "elapsed_time", "")),
                    "location_city": getattr(strava_lib_activity, "location_city", None),
                    "location_state": getattr(strava_lib_activity, "location_state", None),
                    "max_speed": float(getattr(strava_lib_activity, "max_speed", 0) or 0),
                    "average_heartrate": getattr(strava_lib_activity, "average_heartrate", None),
                    "max_heartrate": getattr(strava_lib_activity, "max_heartrate", None),
                    "kilojoules": getattr(strava_lib_activity, "kilojoules", None),
                    "total_elevation_gain": float(getattr(strava_lib_activity, "total_elevation_gain", 0) or 0),
                }
                strava_activity.strava_data = json.dumps(raw_data)
                
                strava_activities.append(strava_activity)
                
            except Exception as e:
                print(f"Error processing Strava activity in fetch: {e}")
                continue

        return strava_activities

    def _fetch_strava_activities_for_month(self, year_month: str):
        """Fetch raw stravalib activities for the given year_month."""
        from dateutil.relativedelta import relativedelta
        import pytz

        year, month = map(int, year_month.split("-"))
        tz = pytz.UTC
        start_date = tz.localize(datetime.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)
        
        activities = []
        for activity in self.client.get_activities(after=start_date, before=end_date, limit=None):
            activities.append(activity)
        
        return activities

    def _convert_to_strava_activity(self, strava_lib_activity) -> StravaActivity:
        """Convert a stravalib activity to our StravaActivity object."""
        strava_activity = StravaActivity()
        
        # Basic fields
        strava_activity.strava_id = str(getattr(strava_lib_activity, "id", ""))
        strava_activity.name = str(getattr(strava_lib_activity, "name", "") or "")
        strava_activity.activity_type = str(getattr(strava_lib_activity, "type", "") or "")
        
        # Distance - convert from meters to miles
        distance_m = getattr(strava_lib_activity, "distance", None)
        if distance_m:
            from decimal import Decimal
            strava_activity.distance = Decimal(str(float(distance_m) * 0.000621371))
        
        # Start time as timestamp string
        start_date = getattr(strava_lib_activity, "start_date", None)
        if start_date:
            strava_activity.start_time = str(int(start_date.timestamp()))
        
        # Duration
        elapsed_time = getattr(strava_lib_activity, "elapsed_time", None)
        if elapsed_time:
            total_seconds = int(elapsed_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            strava_activity.duration_hms = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Location data
        location_city = getattr(strava_lib_activity, "location_city", None)
        if location_city:
            strava_activity.city = str(location_city)
        location_state = getattr(strava_lib_activity, "location_state", None)
        if location_state:
            strava_activity.state = str(location_state)
        
        # Performance metrics
        max_speed = getattr(strava_lib_activity, "max_speed", None)
        if max_speed:
            from decimal import Decimal
            strava_activity.max_speed = Decimal(str(float(max_speed) * 2.237))
        
        avg_hr = getattr(strava_lib_activity, "average_heartrate", None)
        if avg_hr:
            strava_activity.avg_heart_rate = int(avg_hr)
            
        max_hr = getattr(strava_lib_activity, "max_heartrate", None)
        if max_hr:
            strava_activity.max_heart_rate = int(max_hr)
        
        kilojoules = getattr(strava_lib_activity, "kilojoules", None)
        if kilojoules:
            strava_activity.calories = int(float(kilojoules) * 0.239)
        
        # Elevation data
        elev_gain = getattr(strava_lib_activity, "total_elevation_gain", None)
        if elev_gain:
            from decimal import Decimal
            strava_activity.total_elevation_gain = Decimal(str(float(elev_gain) * 3.281))
        
        # Store raw data
        raw_data = {
            "id": getattr(strava_lib_activity, "id", None),
            "name": getattr(strava_lib_activity, "name", None),
            "type": getattr(strava_lib_activity, "type", None),
            "distance": float(getattr(strava_lib_activity, "distance", 0) or 0),
            "start_date": str(getattr(strava_lib_activity, "start_date", "")),
            "elapsed_time": str(getattr(strava_lib_activity, "elapsed_time", "")),
        }
        strava_activity.strava_data = json.dumps(raw_data)
        
        return strava_activity

