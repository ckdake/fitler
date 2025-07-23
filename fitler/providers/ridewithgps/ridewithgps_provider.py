"""RideWithGPS provider for Fitler.

This module defines the RideWithGPSProvider class, which provides an interface
for interacting with RideWithGPS activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
import json
from typing import List, Optional, Dict
from pyrwgps import RideWithGPS
import datetime

from fitler.providers.base_provider import FitnessProvider
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from peewee import DoesNotExist


class RideWithGPSProvider(FitnessProvider):
    def __init__(self):
        self.username = os.environ["RIDEWITHGPS_EMAIL"]
        self.password = os.environ["RIDEWITHGPS_PASSWORD"]
        self.apikey = os.environ["RIDEWITHGPS_KEY"]

        self.client = RideWithGPS(apikey=self.apikey, cache=True)

        user_info = self.client.authenticate(self.username, self.password)
        self.userid = getattr(user_info, "id", None)

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "ridewithgps"

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
                # Query activities that have ridewithgps_id set AND
                # source=ridewithgps for this month
                existing_activities = list(
                    Activity.select().where(
                        (Activity.ridewithgps_id.is_null(False))
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

        # Load config for provider priority
        from pathlib import Path

        config_path = Path("fitler_config.json")
        with open(config_path) as f:
            # Load config but don't use it in this method
            json.load(f)

        persisted_activities = []

        for raw_activity in raw_activities:
            # Convert the raw activity data to a dict for update_from_provider
            activity_data = {
                "id": getattr(raw_activity, "ridewithgps_id", None),
                "name": getattr(raw_activity, "name", None),
                "distance": getattr(raw_activity, "distance", None),
                "equipment": getattr(raw_activity, "equipment", None),
                "activity_type": getattr(raw_activity, "activity_type", None),
                "start_time": getattr(raw_activity, "departed_at", None),
                "notes": getattr(raw_activity, "notes", None),
                # Set source to this provider
                "source": self.provider_name,
            }

            # Look for existing activity with this ridewithgps_id AND source=ridewithgps
            existing_activity = None
            if activity_data["id"]:
                try:
                    existing_activity = Activity.get(
                        (Activity.ridewithgps_id == activity_data["id"])
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
                activity.set_start_time(str(activity_data["start_time"]))

            # Set all the fields directly (handle None values)
            activity.ridewithgps_id = activity_data["id"]
            if activity_data.get("name"):
                activity.name = activity_data["name"]
            if activity_data.get("distance"):
                activity.distance = activity_data["distance"]
            if activity_data.get("equipment"):
                activity.equipment = activity_data["equipment"]
            if activity_data.get("activity_type"):
                activity.activity_type = activity_data["activity_type"]
            if activity_data.get("notes"):
                activity.notes = activity_data["notes"]
            activity.source = self.provider_name

            # Store the raw provider data
            activity.ridewithgps_data = json.dumps(activity_data)

            # Save the activity
            activity.save()
            persisted_activities.append(activity)

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)

        return persisted_activities

    def _parse_ridewithgps_datetime(self, dt_val):
        # RideWithGPS provides datetime strings in ISO8601 format with timezone
        # e.g. '2025-01-02T19:55:14-05:00'
        from dateutil import parser as dt_parser

        if not dt_val:
            return None
        try:
            # Parse the ISO8601 string which includes timezone
            dt = dt_parser.parse(str(dt_val))
            # At this point dt should have the correct timezone (-05:00)
            if dt and dt.tzinfo is None:
                # If somehow we get a naive datetime, assume local
                dt = dt.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
            # Keep the parsed datetime in its original timezone
            return dt
        except Exception:
            return None

    def fetch_activities(self) -> List[Activity]:
        activities = []
        trips = self.client.list(f"/users/{self.userid}/trips.json")
        gear = self.get_gear()
        for trip in trips:
            try:
                departed_at = getattr(trip, "departed_at", None)
                dt = self._parse_ridewithgps_datetime(departed_at)
                if dt:
                    # Convert to UTC and get timestamp
                    utc_dt = dt.astimezone(datetime.timezone.utc)
                    timestamp = str(int(utc_dt.timestamp()))
                else:
                    timestamp = None
                gear_id = getattr(trip, "gear_id", None)
                gear_id_str = str(gear_id) if gear_id is not None else None
                act = Activity(
                    departed_at=timestamp,
                    distance=getattr(trip, "distance", 0)
                    * 0.00062137,  # meters to miles
                    ridewithgps_id=getattr(trip, "id", None),
                    name=getattr(trip, "name", None),
                    notes=getattr(trip, "name", None),
                    equipment=(gear.get(gear_id_str, "") if gear_id_str else ""),
                )
                activities.append(act)
            except Exception as e:
                print("Exception fetching RideWithGPS Activity:", e)
        return activities

    def create_activity(self, activity: Activity) -> str:
        """Create an activity on RideWithGPS (upload a file)."""
        if not activity.source_file:
            raise ValueError("No source file provided for activity upload.")
        with open(activity.source_file, "rb") as file_obj:
            trip = self.client.put(path="/trips", files={"file": file_obj})
        return str(getattr(trip, "id", ""))

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        trip = self.client.get(path=f"/trips/{activity_id}.json")
        if not trip:
            return None
        gear = self.get_gear()
        departed_at = getattr(trip, "departed_at", None)
        dt = self._parse_ridewithgps_datetime(departed_at)
        if dt:
            # Convert to UTC and get timestamp
            utc_dt = dt.astimezone(datetime.timezone.utc)
            timestamp = str(int(utc_dt.timestamp()))
        else:
            timestamp = None
        gear_id = getattr(trip, "gear_id", None)
        gear_id_str = str(gear_id) if gear_id is not None else None
        return Activity(
            departed_at=timestamp,
            distance=getattr(trip, "distance", 0) * 0.00062137,
            ridewithgps_id=getattr(trip, "id", None),
            notes=getattr(trip, "name", None),
            equipment=gear.get(gear_id_str, "") if gear_id_str else "",
        )

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        if not activity.name:
            raise ValueError("No name provided for activity update.")
        updated_trip = self.client.put(
            path=f"/trips/{activity_id}.json", params={"name": activity.name}
        )
        return (
            hasattr(updated_trip, "trip")
            and getattr(updated_trip.trip, "name", None) == activity.name
        )

    def get_gear(self) -> Dict[str, str]:
        gear = {}
        gear_list = self.client.list(path=f"/users/{self.userid}/gear.json")
        for g in gear_list:
            gear_id = getattr(g, "id", None)
            nickname = getattr(g, "nickname", "")
            if gear_id is not None:
                gear[str(gear_id)] = nickname
        return gear

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        updated_trip = self.client.put(
            path=f"/trips/{activity_id}.json", param={"gear_id": gear_id}
        )
        return (
            hasattr(updated_trip, "trip")
            and getattr(updated_trip.trip, "gear_id", None) == gear_id
        )

    def fetch_activities_for_month(self, year_month: str) -> List[Activity]:
        """
        Return activities for the given year_month (YYYY-MM).
        """
        all_activities = self.fetch_activities()
        filtered = []
        year, month = map(int, year_month.split("-"))
        for act in all_activities:
            departed_at = getattr(act, "departed_at", None)
            if departed_at:
                try:
                    # Convert GMT timestamp to local time for filtering
                    dt = datetime.datetime.fromtimestamp(int(departed_at))
                    if dt.year == year and dt.month == month:
                        filtered.append(act)
                except (ValueError, TypeError):
                    continue
        return filtered
