"""RideWithGPS provider for Fitler.

This module defines the RideWithGPSProvider class, which provides an interface
for interacting with RideWithGPS activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
from typing import List, Optional, Dict, Any
from decimal import Decimal
import datetime

from dateutil import parser as dt_parser

from pyrwgps import RideWithGPS

from fitler.providers.base_provider import FitnessProvider
from fitler.provider_sync import ProviderSync
from fitler.providers.ridewithgps.ridewithgps_activity import RideWithGPSActivity


class RideWithGPSProvider(FitnessProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.username = os.environ["RIDEWITHGPS_EMAIL"]
        self.password = os.environ["RIDEWITHGPS_PASSWORD"]
        self.apikey = os.environ["RIDEWITHGPS_KEY"]

        self.client = RideWithGPS(apikey=self.apikey, cache=True)

        user_info = self.client.authenticate(self.username, self.password)
        self.userid = getattr(user_info, "id", None)
        self.user_info = user_info

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "ridewithgps"

    def pull_activities(
        self, date_filter: Optional[str] = None
    ) -> List[RideWithGPSActivity]:
        """
        Pull activities from RideWithGPS for a given month (YYYY-MM).
        Only activities for the specified month are fetched and persisted.
        """
        if date_filter is None:
            print("RideWithGPS provider: pulling all activities not implemented yet")
            return []

        year, month = map(int, date_filter.split("-"))

        if not ProviderSync.get_or_none(date_filter, self.provider_name):
            trip_summaries = list(self.client.list(f"/users/{self.userid}/trips.json"))
            print(f"Found {len(trip_summaries)} RideWithGPS trip summaries")

            for trip_summary in trip_summaries:
                try:
                    trip_id = trip_summary.id
                    departed_at = trip_summary.departed_at
                    if not trip_id or not departed_at:
                        continue
                    # Parse date string to datetime
                    dt = self._parse_iso8601(departed_at)
                    if not dt:
                        continue
                    dt_utc = dt.astimezone(datetime.timezone.utc)
                    if dt_utc.year != year or dt_utc.month != month:
                        continue
                    timestamp = int(dt_utc.timestamp())

                    trip = self.client.get(path=f"/trips/{trip_id}.json").trip

                    rwgps_activity = RideWithGPSActivity()

                    rwgps_activity.ridewithgps_id = str(trip.id)
                    rwgps_activity.name = str(trip.name)
                    if hasattr(trip, "distance") and trip.distance is not None:
                        # Convert meters to miles
                        miles = float(trip.distance) / 1609.34
                        rwgps_activity.distance = Decimal(str(miles))
                    rwgps_activity.start_time = timestamp
                    if hasattr(trip, "locality") and trip.locality:
                        rwgps_activity.city = str(trip.locality)
                    if (
                        hasattr(trip, "administrative_area")
                        and trip.administrative_area
                    ):
                        rwgps_activity.state = str(trip.administrative_area)
                    if (
                        hasattr(trip, "gear")
                        and trip.gear
                        and hasattr(trip.gear, "name")
                    ):
                        rwgps_activity.equipment = str(trip.gear.name)
                    existing = RideWithGPSActivity.get_or_none(
                        RideWithGPSActivity.ridewithgps_id == str(trip.id)
                    )
                    if existing:
                        continue
                    try:
                        rwgps_activity.save()
                    except Exception as e:
                        print(f"Error saving RideWithGPS activity {trip.id}: {e}")
                except Exception as e:
                    print(f"Error processing RideWithGPS activity: {e}")
                    continue

            ProviderSync.create(year_month=date_filter, provider=self.provider_name)
            print(f"RideWithGPS Sync complete for {date_filter}")

        # Always return all activities for this month from the database
        start = datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)
        if month == 12:
            end = datetime.datetime(year + 1, 1, 1, tzinfo=datetime.timezone.utc)
        else:
            end = datetime.datetime(year, month + 1, 1, tzinfo=datetime.timezone.utc)
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        activities = list(
            RideWithGPSActivity.select().where(
                (RideWithGPSActivity.start_time >= start_ts)
                & (RideWithGPSActivity.start_time < end_ts)
            )
        )
        return activities

    # Abstract method implementations
    def create_activity(self, activity_data: Dict) -> RideWithGPSActivity:
        """Create a new RideWithGPSActivity from activity data."""
        # Create new activity
        return RideWithGPSActivity.create(**activity_data)

    def get_activity_by_id(self, activity_id: str) -> Optional[RideWithGPSActivity]:
        """Get a RideWithGPSActivity by its provider ID."""
        return RideWithGPSActivity.get_or_none(
            RideWithGPSActivity.ridewithgps_id == activity_id
        )

    def update_activity(self, activity_data: Dict) -> RideWithGPSActivity:
        """Update an existing RideWithGPSActivity with new data."""
        provider_id = activity_data["ridewithgps_id"]
        activity = RideWithGPSActivity.get(
            RideWithGPSActivity.ridewithgps_id == provider_id
        )
        for key, value in activity_data.items():
            setattr(activity, key, value)
        activity.save()
        return activity

    def get_all_gear(self) -> Dict[str, str]:
        """Get gear from RideWithGPS - return empty dict for now."""
        # TODO: Implement gear fetching from RideWithGPS API
        return {}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("Setting gear on RideWithGPS not implemented")

    # Minimal ISO8601 parser helper (required for date filtering)
    def _parse_iso8601(self, dt_val):
        if not dt_val:
            return None

        try:
            return dt_parser.parse(str(dt_val))
        except Exception:
            return None
