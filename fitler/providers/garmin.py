"""Garmin provider for Fitler.

This module defines the GarminProvider class, which provides an interface
for interacting with Garmin Connect activity data, including fetching,
creating, updating activities, and managing gear.
"""

import os
from typing import List, Optional, Dict
import json
import datetime

import garminconnect
from garth.exc import GarthHTTPError
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from fitler.providers.base import FitnessProvider
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from peewee import DoesNotExist


class GarminProvider(FitnessProvider):
    """Provider for Garmin Connect activities."""

    def __init__(self):
        """Initialize GarminProvider with environment credentials."""
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

    def pull_activities(self, date_filter: str) -> List[Activity]:
        """
        Sync activities for a given month filter in YYYY-MM format.
        Returns a list of synced Activity objects that have been persisted to the database.
        """
        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if existing_sync:
            # Return activities from database for this month
            try:
                # Query activities that have garmin_id set AND source=garmin for this month
                existing_activities = list(
                    Activity.select().where(
                        (Activity.garmin_id.is_null(False))
                        & (Activity.source == self.provider_name)
                    )
                )

                # Filter by month in Python since date comparison is tricky
                year, month = map(int, date_filter.split("-"))
                filtered_activities = []
                for act in existing_activities:
                    if act.date and act.date.year == year and act.date.month == month:
                        filtered_activities.append(act)

                print(
                    f"Found {len(filtered_activities)} existing activities "
                    f"from database for {self.provider_name}"
                )
                return filtered_activities
            except Exception as e:
                print(f"Error loading existing activities: {e}")
                # Fall through to re-sync

        # Get the raw activity data for the month
        raw_activities = self.fetch_activities_for_month(date_filter)

        persisted_activities = []

        for raw_activity in raw_activities:
            # Convert the raw activity data to a dict
            activity_data = {
                "id": raw_activity.get("activityId"),
                "name": raw_activity.get("activityName"),
                "distance": raw_activity.get("distance"),  # meters
                "activity_type": raw_activity.get("activityType", {}).get("typeKey"),
                "start_time": raw_activity.get("startTimeGMT"),
                "location_name": raw_activity.get("locationName"),
                "duration": raw_activity.get("duration"),  # seconds
                "max_speed": raw_activity.get("maxSpeed"),
                "avg_heart_rate": raw_activity.get("averageHR"),
                "max_heart_rate": raw_activity.get("maxHR"),
                "calories": raw_activity.get("calories"),
                "max_elevation": raw_activity.get("maxElevation"),
                "total_elevation_gain": raw_activity.get("elevationGain"),
                "avg_cadence": (
                    raw_activity.get("averageRunCadence")
                    or raw_activity.get("averageBikingCadence")
                ),
                "source": self.provider_name,
            }

            # Look for existing activity with this garmin_id AND source=garmin
            existing_activity = None
            if activity_data["id"]:
                try:
                    existing_activity = Activity.get(
                        (Activity.garmin_id == activity_data["id"])
                        & (Activity.source == self.provider_name)
                    )
                except DoesNotExist:
                    existing_activity = None

            if existing_activity:
                # Update existing activity
                activity = existing_activity
            else:
                # Create new activity
                activity = Activity()

            # Set the start time if available
            if activity_data.get("start_time"):
                activity.set_start_time(activity_data["start_time"])

            # Set all the fields directly
            activity.garmin_id = activity_data["id"]
            if activity_data.get("name"):
                activity.name = activity_data["name"]
            if activity_data.get("distance"):
                # Convert meters to miles
                activity.distance = activity_data["distance"] / 1609.34
            if activity_data.get("activity_type"):
                activity.activity_type = activity_data["activity_type"]
            if activity_data.get("location_name"):
                activity.location_name = activity_data["location_name"]
            if activity_data.get("duration"):
                # Convert duration seconds to HH:MM:SS format for duration_hms field
                duration_seconds = activity_data["duration"]
                if duration_seconds:
                    hours = int(duration_seconds // 3600)
                    minutes = int((duration_seconds % 3600) // 60)
                    seconds = int(duration_seconds % 60)
                    activity.duration_hms = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if activity_data.get("max_speed"):
                activity.max_speed = activity_data["max_speed"]
            if activity_data.get("avg_heart_rate"):
                activity.avg_heart_rate = activity_data["avg_heart_rate"]
            if activity_data.get("max_heart_rate"):
                activity.max_heart_rate = activity_data["max_heart_rate"]
            if activity_data.get("calories"):
                activity.calories = activity_data["calories"]
            if activity_data.get("max_elevation"):
                activity.max_elevation = activity_data["max_elevation"]
            if activity_data.get("total_elevation_gain"):
                activity.total_elevation_gain = activity_data["total_elevation_gain"]
            if activity_data.get("avg_cadence"):
                activity.avg_cadence = activity_data["avg_cadence"]
            activity.source = self.provider_name

            # Store the raw provider data
            activity.garmin_data = json.dumps(raw_activity)

            # Save the activity
            activity.save()
            persisted_activities.append(activity)

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)

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

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def get_gear(self) -> Dict[str, str]:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def create_activity(self, activity: Activity) -> str:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")
