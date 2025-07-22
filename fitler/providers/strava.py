"""Strava provider for Fitler.

This module defines the StravaProvider class, which provides an interface
for interacting with Strava activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
import time
import logging
from typing import List, Optional, Dict
import dateparser
import calendar
import datetime
import json
from pathlib import Path

from fitler.providers.base import FitnessProvider
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from peewee import DoesNotExist


class StravaProvider(FitnessProvider):
    def __init__(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_expires: Optional[str] = None,
    ):
        # Initialize debug from environment and config
        self.debug = os.environ.get("STRAVALIB_DEBUG") == "1"
        if not self.debug:
            try:
                with open("fitler_config.json") as f:
                    config = json.load(f)
                    self.debug = config.get("debug", False)
            except Exception:
                pass

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
                # Query activities that have strava_id set AND source=strava for this month
                existing_activities = list(
                    Activity.select().where(
                        (Activity.strava_id.is_null(False))
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
                    f"Found {len(filtered_activities)} existing activities from database for {self.provider_name}"
                )
                return filtered_activities
            except Exception as e:
                print(f"Error loading existing activities: {e}")
                # Fall through to re-sync

        # Get the raw activity data for the month
        raw_activities = self.fetch_activities_for_month(date_filter)

        # Load config for provider priority
        from pathlib import Path
        import json

        config_path = Path("fitler_config.json")
        with open(config_path) as f:
            config = json.load(f)

        persisted_activities = []

        for raw_activity in raw_activities:
            # Convert the raw activity data to a dict for update_from_provider
            activity_data = {
                "id": getattr(raw_activity, "strava_id", None),
                "name": getattr(raw_activity, "name", None),
                "distance": getattr(raw_activity, "distance", None),
                "equipment": getattr(raw_activity, "equipment", None),
                "activity_type": getattr(raw_activity, "activity_type", None),
                "start_time": getattr(raw_activity, "departed_at", None),
                "notes": getattr(raw_activity, "notes", None),
                # Set source to this provider
                "source": self.provider_name,
            }

            # Look for existing activity with this strava_id AND source=strava
            existing_activity = None
            if activity_data["id"]:
                try:
                    existing_activity = Activity.get(
                        (Activity.strava_id == activity_data["id"])
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
            activity.strava_id = activity_data["id"]
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
            import json

            activity.strava_data = json.dumps(activity_data)

            # Save the activity
            activity.save()
            persisted_activities.append(activity)

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)

        return persisted_activities

    def _get_gmt_timestamp(self, dt_str):
        """Convert a datetime string to a GMT Unix timestamp.
        Strava's start_date_local is in the activity's local timezone."""
        if not dt_str:
            return None
        try:
            # Import here to avoid circular imports
            from pathlib import Path
            import json
            from zoneinfo import ZoneInfo

            # Get home timezone from config
            config_path = Path("fitler_config.json")
            with open(config_path) as f:
                config = json.load(f)
            home_tz = ZoneInfo(config.get("home_timezone", "US/Eastern"))

            dt = dateparser.parse(str(dt_str))
            if dt:
                if dt.tzinfo is None:
                    # If no timezone, assume it's in home timezone (where the activity was recorded)
                    dt = dt.replace(tzinfo=home_tz)
                # Convert to UTC timestamp
                utc_dt = dt.astimezone(datetime.timezone.utc)
                return str(int(utc_dt.timestamp()))
        except Exception:
            return None
        return None

    def fetch_activities(self) -> List[Activity]:
        activities = []
        for a in self.client.get_activities():
            try:
                start_date_local = getattr(a, "start_date_local", None)
                if not start_date_local:
                    continue
                # Convert to GMT timestamp
                departed_at = self._get_gmt_timestamp(start_date_local)
                act = Activity(
                    name=getattr(a, "name", None),
                    departed_at=departed_at,
                    distance=getattr(a, "distance", 0) * 0.00062137,
                    strava_id=getattr(a, "id", None),
                    notes=getattr(a, "name", None),
                )
                activities.append(act)
            except Exception:
                continue
        return activities

    def create_activity(self, activity: Activity) -> str:
        # Implement upload logic if needed
        raise NotImplementedError("Strava create_activity not implemented.")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Fetch a single activity by its Strava ID."""
        try:
            activity = self.client.get_activity(int(activity_id))
            if not activity:
                return None
            start_date_local = getattr(activity, "start_date_local", None)
            name = getattr(activity, "name", None)
            if not start_date_local:
                return None
            # Convert to GMT timestamp
            departed_at = self._get_gmt_timestamp(start_date_local)

            # Get gear details from Strava API
            gear_id = getattr(activity, "gear_id", None)
            gear_name = ""
            if gear_id:
                try:
                    gear = self.client.get_gear(gear_id)
                    if gear and hasattr(gear, "name"):
                        gear_name = str(
                            gear.name
                        )  # Convert to string in case it's a special type
                        gear_name = self._clean_gear_name(gear_name)
                except Exception as e:
                    if self.debug:
                        print(f"DEBUG: Error fetching gear details: {e}")

            if self.debug:
                print("\nDEBUG: Gear details:")
                print(f"DEBUG:   gear_id = {gear_id}")
                print(f"DEBUG:   final gear_name = {gear_name}\n")

            act = Activity(
                name=name,
                departed_at=departed_at,
                distance=getattr(activity, "distance", 0) * 0.00062137,
                strava_id=getattr(activity, "id", None),
                equipment=gear_name,
            )
            return act
        except Exception as e:
            logging.warning("Error fetching Strava activity: %s", e)
            return None

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        # Not implemented for Strava
        raise NotImplementedError("Strava update_activity not implemented.")

    def get_gear(self) -> Dict[str, str]:
        # Not implemented for Strava
        return {}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        # Not implemented for Strava
        raise NotImplementedError("Strava set_gear not implemented.")

    def fetch_activities_for_month(self, year_month: str) -> List[Activity]:
        """
        Return activities for the given year_month (YYYY-MM) using Stravalib API filters and pagination.
        """
        from dateutil.relativedelta import relativedelta
        import pytz

        year, month = map(int, year_month.split("-"))
        tz = pytz.UTC
        start_date = tz.localize(datetime.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)
        activities = []
        # Use None for all optional params to ensure we get full activity details
        for a in self.client.get_activities(
            after=start_date, before=end_date, limit=None
        ):
            try:
                start_date_local = getattr(a, "start_date_local", None)
                if self.debug:
                    print(
                        f"DEBUG: id={getattr(a, 'id', None)}, name={getattr(a, 'name', None)}, start_date_local={start_date_local} type={type(start_date_local)}"
                    )
                if not start_date_local:
                    continue
                if isinstance(start_date_local, str):
                    parsed_date = dateparser.parse(start_date_local)
                elif isinstance(start_date_local, datetime.datetime):
                    parsed_date = start_date_local
                else:
                    if self.debug:
                        print(
                            f"DEBUG: Unhandled start_date_local type: {type(start_date_local)}"
                        )
                    continue

                if not parsed_date:
                    continue

                # Convert to UTC and get timestamp
                # Get home timezone from config for local times
                from zoneinfo import ZoneInfo

                config_path = Path("fitler_config.json")
                with open(config_path) as f:
                    config = json.load(f)
                home_tz = ZoneInfo(config.get("home_timezone", "US/Eastern"))

                if parsed_date.tzinfo is None:
                    # If no timezone, assume it's in home timezone
                    parsed_date = parsed_date.replace(tzinfo=home_tz)
                utc_dt = parsed_date.astimezone(datetime.timezone.utc)
                departed_at = str(int(utc_dt.timestamp()))

                # Still use the UTC date range for filtering
                if not (start_date <= utc_dt < end_date):
                    continue

                # In debug mode, dump all available activity attributes
                if self.debug:
                    print("\nDEBUG: Activity details:")
                    for attr in dir(a):
                        if not attr.startswith("_"):  # Skip internal attributes
                            try:
                                val = getattr(a, attr)
                                print(f"DEBUG:   {attr} = {val} (type: {type(val)})")
                            except Exception as e:
                                print(f"DEBUG:   {attr} error: {e}")

                # Get gear details from Strava API
                gear_id = getattr(a, "gear_id", None)
                gear_name = ""
                if gear_id:
                    try:
                        gear = self.client.get_gear(gear_id)
                        if gear and hasattr(gear, "name"):
                            gear_name = str(
                                gear.name
                            )  # Convert to string in case it's a special type
                            gear_name = self._clean_gear_name(gear_name)
                    except Exception as e:
                        if self.debug:
                            print(f"DEBUG: Error fetching gear details: {e}")

                if self.debug:
                    print("\nDEBUG: Gear details:")
                    print(f"DEBUG:   gear_id = {gear_id}")
                    print(f"DEBUG:   final gear_name = {gear_name}\n")

                act = Activity(
                    name=getattr(a, "name", None),
                    departed_at=departed_at,
                    distance=getattr(a, "distance", 0) * 0.00062137,
                    strava_id=getattr(a, "id", None),
                    notes=getattr(a, "name", None),
                    equipment=gear_name,
                )
                activities.append(act)
            except Exception as e:
                if self.debug:
                    print(f"DEBUG: Exception processing activity: {e}")
                continue
        return activities

    def _clean_gear_name(self, gear_name: str) -> str:
        """Clean up gear names that have duplication with year in them.
        Example: "Altra Escalante 4 2025 Altra Escalante 4" -> "2025 Altra Escalante 4"
        Does not modify names that already start with a year like "2006 Redline 925"
        """
        if not gear_name:
            return gear_name

        # Check if the name already starts with a year (YYYY)
        import re

        if re.match(r"^\s*20\d{2}\b", gear_name):
            return gear_name

        # Look for a year in the middle of the string
        year_match = re.search(r"\b(20\d{2})\b", gear_name)
        if year_match:
            year = year_match.group(1)
            # Split the string by the year
            parts = gear_name.split(year)
            if len(parts) == 2:
                # Get the shorter part (assumes the duplicate is longer)
                base_name = min(parts[0].strip(), parts[1].strip(), key=len)
                # Return in format "YYYY Base Name"
                return f"{year} {base_name}".strip()
        return gear_name
