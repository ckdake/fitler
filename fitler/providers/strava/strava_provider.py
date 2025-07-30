"""Strava provider for Fitler."""

import os
import logging
from typing import List, Optional, Dict, Any
import datetime

from fitler.providers.base_provider import FitnessProvider
from fitler.provider_sync import ProviderSync
from fitler.providers.strava.strava_activity import StravaActivity


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

        self.debug = os.environ.get("STRAVALIB_DEBUG") == "1"
        if not self.debug and self.config:
            self.debug = self.config.get("debug", False)

        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

        from stravalib import Client

        self.client = Client(access_token=token)

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "strava"

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
                    strava_activity = self._convert_to_strava_activity(strava_lib_activity)

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

    def _get_strava_activities_for_month(self, date_filter: str) -> List["StravaActivity"]:
        """Get StravaActivity objects for a specific month."""
        from fitler.providers.strava.strava_activity import StravaActivity
        import datetime

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
        from dateutil.relativedelta import relativedelta
        import pytz

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
        """Convert a stravalib activity to our StravaActivity object, always fetching full details for gear info."""
        import json
        from decimal import Decimal

        strava_activity = StravaActivity()

        # Always fetch the full activity details to ensure gear info is present
        activity_id = getattr(strava_lib_activity, "id", None)
        full_activity = strava_lib_activity
        try:
            # Use the client to fetch full activity details (includes gear)
            full_activity = self.client.get_activity(activity_id)
        except Exception:
            pass  # fallback to the original object if API call fails

        # Basic fields
        setattr(strava_activity, "strava_id", str(getattr(full_activity, "id", "")))
        setattr(strava_activity, "name", str(getattr(full_activity, "name", "") or ""))
        setattr(strava_activity, "activity_type", str(getattr(full_activity, "type", "") or ""))

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
                setattr(strava_activity, "equipment", str(gear_name))

        # Store raw data as full activity JSON
        if hasattr(full_activity, 'model_dump'):
            raw_data = full_activity.model_dump()
        elif hasattr(full_activity, 'dict'):
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

    def update_activity(self, activity_data: Dict[str, Any]) -> StravaActivity:
        """Update an existing StravaActivity with new data."""
        provider_id = activity_data["strava_id"]
        activity = StravaActivity.get(StravaActivity.strava_id == provider_id)
        for key, value in activity_data.items():
            setattr(activity, key, value)
        activity.save()
        return activity

    def get_gear(self) -> Dict[str, str]:
        raise NotImplementedError("Getting gear from Strava not implemented")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("Setting gear on Strava not implemented")
