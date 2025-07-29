"""Garmin provider for Fitler.

This module defines the GarminProvider class, which provides an interface
for interacting with Garmin Connect activity data, including fetching,
creating, updating activities, and managing gear.
"""

import os
from typing import List, Optional, Dict, Any
import json
import datetime

import garminconnect
from garth.exc import GarthHTTPError
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from fitler.providers.base_provider import FitnessProvider
from fitler.provider_sync import ProviderSync
from fitler.providers.garmin.garmin_activity import GarminActivity
from peewee import DoesNotExist


class GarminProvider(FitnessProvider):
    """Provider for Garmin Connect activities."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GarminProvider with environment credentials."""
        super().__init__(config)
        self.email = os.environ.get("GARMIN_EMAIL", "")
        self.tokenstore = os.environ.get("GARMINTOKENS", "~/.garminconnect")
        self.client = None

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "garmin"

    def _get_client(self):
        """Get authenticated Garmin client."""
        if self.client is None:
            try:
                # Try to login with existing tokens
                self.client = garminconnect.Garmin()
                self.client.login(self.tokenstore)
            except Exception as e:
                raise Exception(
                    f"Garmin authentication failed: {e}. "
                    f"Please run 'python -m fitler auth-garmin' first."
                )
        return self.client

    def pull_activities(
        self, date_filter: Optional[str] = None
    ) -> List[GarminActivity]:
        """
        Sync activities for a given month filter in YYYY-MM format.
        If date_filter is None, pulls all activities (not implemented yet).
        Returns a list of synced GarminActivity objects that have been persisted to the database.
        """
        # For now, require date_filter
        if date_filter is None:
            print("Garmin provider: pulling all activities not implemented yet")
            return []

        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if not existing_sync:
            # First time processing this month - fetch from Garmin API
            raw_activities = self.fetch_activities_for_month(date_filter)
        print(f"Found {len(raw_activities)} Garmin activities for {date_filter}")

        persisted_activities = []

        for raw_activity in raw_activities:
            try:
                # Create GarminActivity from raw data
                garmin_activity = GarminActivity()

                # Set basic activity data (raw_activity is a dict from Garmin API)
                garmin_activity.garmin_id = str(raw_activity.get("activityId", ""))
                garmin_activity.name = str(raw_activity.get("activityName", ""))

                # Activity type
                activity_type_info = raw_activity.get("activityType", {})
                if isinstance(activity_type_info, dict):
                    garmin_activity.activity_type = str(
                        activity_type_info.get("typeKey", "")
                    )
                else:
                    garmin_activity.activity_type = str(activity_type_info or "")

                # Distance conversion from meters to miles
                if raw_activity.get("distance"):
                    from decimal import Decimal

                    distance_meters = float(raw_activity.get("distance", 0))
                    garmin_activity.distance = Decimal(
                        str(distance_meters * 0.000621371)
                    )

                # Start time
                if raw_activity.get("startTimeGMT"):
                    # Convert Garmin timestamp to epoch
                    start_time_str = raw_activity.get("startTimeGMT")
                    # Handle Garmin timestamp format
                    import dateutil.parser

                    dt = dateutil.parser.parse(start_time_str)
                    garmin_activity.start_time = int(dt.timestamp())

                # Duration
                if raw_activity.get("duration"):
                    total_seconds = int(raw_activity.get("duration", 0))
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    garmin_activity.duration_hms = (
                        f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    )

                # Location data
                if raw_activity.get("locationName"):
                    garmin_activity.location_name = str(
                        raw_activity.get("locationName", "")
                    )

                # Performance metrics
                if raw_activity.get("maxSpeed"):
                    from decimal import Decimal

                    # Convert m/s to mph
                    max_speed_ms = float(raw_activity.get("maxSpeed", 0))
                    garmin_activity.max_speed = Decimal(str(max_speed_ms * 2.237))

                if raw_activity.get("averageHR"):
                    garmin_activity.avg_heart_rate = int(
                        raw_activity.get("averageHR", 0)
                    )

                if raw_activity.get("maxHR"):
                    garmin_activity.max_heart_rate = int(raw_activity.get("maxHR", 0))

                if raw_activity.get("calories"):
                    garmin_activity.calories = int(raw_activity.get("calories", 0))

                # Store raw data as JSON
                garmin_activity.raw_data = json.dumps(raw_activity)

                # Check for duplicates based on garmin_id
                existing = GarminActivity.get_or_none(
                    GarminActivity.garmin_id == str(raw_activity.get("activityId", ""))
                )
                if existing:
                    print(
                        f"Skipping duplicate Garmin activity {raw_activity.get('activityId')}"
                    )
                    continue

                # Save to garmin_activities table
                garmin_activity.save()
                persisted_activities.append(garmin_activity)

            except Exception as e:
                print(f"Error processing Garmin activity: {e}")
                continue

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)

        print(
            f"Synced {len(persisted_activities)} Garmin activities to garmin_activities table"
        )
        return persisted_activities

    def fetch_activities_for_month(self, year_month: str) -> List[Dict]:
        """
        Return activities for the given year_month (YYYY-MM) using Garmin Connect API.
        """
        client = self._get_client()

        # Parse year and month
        year, month = map(int, year_month.split("-"))

        # Get start and end dates for the month
        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        try:
            # Get activities for the date range
            activities = client.get_activities_by_date(
                start_date.isoformat(), end_date.isoformat()
            )

            print(
                f"Found {len(activities)} activities from Garmin Connect for {year_month}"
            )
            return activities

        except (
            GarminConnectAuthenticationError,
            GarminConnectConnectionError,
            GarminConnectTooManyRequestsError,
            GarthHTTPError,
        ) as err:
            print(f"Error fetching activities from Garmin: {err}")
            return []

    def get_activity_by_id(self, activity_id: str) -> Optional[GarminActivity]:
        """Get a GarminActivity by its provider ID."""
        return GarminActivity.get_or_none(GarminActivity.garmin_id == activity_id)

    def update_activity(self, activity_data: Dict) -> GarminActivity:
        """Update an existing GarminActivity with new data."""
        provider_id = activity_data["garmin_id"]
        activity = GarminActivity.get(GarminActivity.garmin_id == provider_id)
        for key, value in activity_data.items():
            setattr(activity, key, value)
        activity.save()
        return activity

    def get_gear(self) -> Dict[str, str]:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def create_activity(self, activity_data: Dict) -> GarminActivity:
        """Create a new GarminActivity from activity data."""
        return GarminActivity.create(**activity_data)

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")
