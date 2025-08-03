"""Strava provider for Fitler."""

import os
import re
import logging
from typing import List, Optional, Dict, Any
import datetime
import json
from decimal import Decimal
import time

from dateutil.relativedelta import relativedelta
import pytz

from stravalib import Client

from fitler.providers.base_provider import FitnessProvider
from fitler.provider_sync import ProviderSync
from fitler.providers.strava.strava_activity import StravaActivity


class StravaProvider(FitnessProvider):
    def __init__(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        token_expires: Optional[str] = "0",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)

        self.debug = os.environ.get("STRAVALIB_DEBUG") == "1"
        if not self.debug and self.config:
            self.debug = self.config.get("debug", False)

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

        self.client = Client(
            access_token=token,
            refresh_token=refresh_token,
            token_expires=int(token_expires),
        )

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "strava"

    @staticmethod
    def _normalize_strava_gear_name(gear_name: str) -> str:
        """
        Extracts the year (YYYY) and the word(s) before it from a Strava gear name,
        and returns a string in the format 'YYYY EquipmentName'.
        If the gear name already starts with the year, return it unchanged.
        """
        match = re.search(r"(\b\d{4}\b)", gear_name)
        if match:
            year = match.group(1)
            before_year = gear_name[: match.start()].strip()
            # If the gear name already starts with the year, return as is
            if gear_name.strip().startswith(year):
                return gear_name
            return f"{year} {before_year}"
        return gear_name

    def pull_activities(
        self, date_filter: Optional[str] = None
    ) -> List[StravaActivity]:
        """Pull activities from Strava API for the given date filter."""
        if date_filter is None:
            print("Strava provider: pulling all activities not implemented yet")
            return []

        # Check if already synced
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if not existing_sync:
            # First time processing this month - fetch from Strava API
            raw_activities = self._fetch_strava_activities_for_month(date_filter)
            print(f"Found {len(raw_activities)} Strava activities for {date_filter}")

            processed_count = 0
            for strava_lib_activity in raw_activities:
                try:
                    # Convert stravalib activity to our StravaActivity
                    strava_activity = self._convert_to_strava_activity(
                        strava_lib_activity
                    )

                    # Check for duplicates
                    existing = StravaActivity.get_or_none(
                        StravaActivity.strava_id == strava_activity.strava_id
                    )
                    if existing:
                        continue

                    # Save to database
                    strava_activity.save()
                    processed_count += 1

                except Exception as e:
                    print(f"Error processing Strava activity: {e}")
                    continue

            # Mark this month as synced
            ProviderSync.create(year_month=date_filter, provider=self.provider_name)
            print(f"Synced {processed_count} Strava activities")
        else:
            print(f"Month {date_filter} already synced for {self.provider_name}")

        # Always return activities for the requested month from database
        return self._get_strava_activities_for_month(date_filter)

    def _get_strava_activities_for_month(
        self, date_filter: str
    ) -> List["StravaActivity"]:
        """Get StravaActivity objects for a specific month."""

        year, month = map(int, date_filter.split("-"))
        strava_activities = []

        for activity in StravaActivity.select():
            if hasattr(activity, "start_time") and activity.start_time:
                try:
                    # Convert timestamp to datetime for comparison
                    dt = datetime.datetime.fromtimestamp(int(activity.start_time))
                    if dt.year == year and dt.month == month:
                        strava_activities.append(activity)
                except (ValueError, TypeError):
                    continue

        return strava_activities

    def _fetch_strava_activities_for_month(self, year_month: str):
        """Fetch raw stravalib activities for the given year_month."""
        year, month = map(int, year_month.split("-"))
        tz = pytz.UTC
        start_date = tz.localize(datetime.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)

        activities = []
        for activity in self.client.get_activities(
            after=start_date, before=end_date, limit=None
        ):
            activities.append(activity)

        return activities

    def _convert_to_strava_activity(self, strava_lib_activity) -> StravaActivity:
        """Convert a stravalib activity to our StravaActivity object"""
        strava_activity = StravaActivity()

        activity_id = getattr(strava_lib_activity, "id", None)
        full_activity = strava_lib_activity

        if activity_id is not None:
            time.sleep(1)  # Throttle API calls to avoid rate limit
            full_activity = self.client.get_activity(int(activity_id))

        # Basic fields
        setattr(strava_activity, "strava_id", str(getattr(full_activity, "id", "")))
        setattr(strava_activity, "name", str(getattr(full_activity, "name", "") or ""))
        setattr(
            strava_activity,
            "activity_type",
            str(getattr(full_activity, "type", "") or ""),
        )

        # Distance - convert from meters to miles
        distance_m = getattr(full_activity, "distance", None)
        if distance_m:
            setattr(
                strava_activity,
                "distance",
                Decimal(str(float(distance_m) * 0.000621371)),
            )

        # Start time as timestamp string
        start_date = getattr(full_activity, "start_date", None)
        if start_date:
            setattr(strava_activity, "start_time", int(start_date.timestamp()))

        # Duration
        elapsed_time = getattr(full_activity, "elapsed_time", None)
        if elapsed_time:
            if hasattr(elapsed_time, "total_seconds"):
                total_seconds = int(elapsed_time.total_seconds())
            elif hasattr(elapsed_time, "seconds"):
                total_seconds = int(elapsed_time.seconds)
            else:
                total_seconds = int(elapsed_time)

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            setattr(
                strava_activity,
                "duration_hms",
                f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            )

        # Equipment/gear information
        gear = getattr(full_activity, "gear", None)
        if gear and hasattr(gear, "name"):
            gear_name = getattr(gear, "name", None)
            if gear_name:
                setattr(
                    strava_activity,
                    "equipment",
                    self._normalize_strava_gear_name(str(gear_name)),
                )

        # Store raw data as full activity JSON
        if hasattr(full_activity, "model_dump"):
            raw_data = full_activity.model_dump()
        elif hasattr(full_activity, "dict"):
            raw_data = full_activity.dict()
        else:
            raw_data = dict(full_activity)
        setattr(strava_activity, "raw_data", json.dumps(raw_data, default=str))

        return strava_activity

    # Abstract method implementations
    def create_activity(self, activity_data: Dict[str, Any]) -> StravaActivity:
        """Create a new StravaActivity from activity data."""
        return StravaActivity.create(**activity_data)

    def get_activity_by_id(self, activity_id: str) -> Optional[StravaActivity]:
        """Get a StravaActivity by its provider ID."""
        return StravaActivity.get_or_none(StravaActivity.strava_id == activity_id)

    def update_activity(self, activity_data: Dict[str, Any]) -> bool:
        """Update an existing Strava activity via API."""
        provider_id = activity_data["strava_id"]
        
        try:
            # Remove the provider_id from the data before sending to API
            update_data = {k: v for k, v in activity_data.items() if k != "strava_id"}
            
            # Use stravalib to update the activity
            self.client.update_activity(activity_id=int(provider_id), **update_data)
            
            return True
                    
        except Exception as e:
            print(f"Error updating Strava activity {provider_id}: {e}")
            return False

    def get_all_gear(self) -> Dict[str, str]:
        raise NotImplementedError("Getting gear from Strava not implemented")

    def set_gear(self, gear_name: str, activity_id: str) -> bool:
        raise NotImplementedError("Setting gear on Strava not implemented")
