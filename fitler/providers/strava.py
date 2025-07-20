"""Strava provider for Fitler.

This module defines the StravaActivities class, which provides an interface
for interacting with Strava activity data, including fetching, creating,
and updating activities, as well as managing gear.
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

from fitler.providers.base import FitnessProvider, Activity


class StravaActivities(FitnessProvider):
    def __init__(self, token: str, refresh_token: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None, token_expires: Optional[str] = None):
        if os.environ.get("STRAVALIB_DEBUG") == "1":
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
            home_tz = ZoneInfo(config.get('home_timezone', 'US/Eastern'))

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
            act = Activity(
                name=name,
                departed_at=departed_at,
                distance=getattr(activity, "distance", 0) * 0.00062137,
                strava_id=getattr(activity, "id", None)
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
        debug = os.environ.get("STRAVALIB_DEBUG") == "1"

        year, month = map(int, year_month.split("-"))
        tz = pytz.UTC
        start_date = tz.localize(datetime.datetime(year, month, 1))
        end_date = start_date + relativedelta(months=1)
        activities = []
        for a in self.client.get_activities(after=start_date, before=end_date):
            try:
                start_date_local = getattr(a, "start_date_local", None)
                if debug:
                    print(f"DEBUG: id={getattr(a, 'id', None)}, name={getattr(a, 'name', None)}, start_date_local={start_date_local} type={type(start_date_local)}")
                if not start_date_local:
                    continue
                if isinstance(start_date_local, str):
                    parsed_date = dateparser.parse(start_date_local)
                elif isinstance(start_date_local, datetime.datetime):
                    parsed_date = start_date_local
                else:
                    if debug:
                        print(f"DEBUG: Unhandled start_date_local type: {type(start_date_local)}")
                    continue
                
                if not parsed_date:
                    continue

                # Convert to UTC and get timestamp
                # Get home timezone from config for local times
                from zoneinfo import ZoneInfo
                config_path = Path("fitler_config.json")
                with open(config_path) as f:
                    config = json.load(f)
                home_tz = ZoneInfo(config.get('home_timezone', 'US/Eastern'))

                if parsed_date.tzinfo is None:
                    # If no timezone, assume it's in home timezone
                    parsed_date = parsed_date.replace(tzinfo=home_tz)
                utc_dt = parsed_date.astimezone(datetime.timezone.utc)
                departed_at = str(int(utc_dt.timestamp()))

                # Still use the UTC date range for filtering
                if not (start_date <= utc_dt < end_date):
                    continue

                act = Activity(
                    name=getattr(a, "name", None),
                    departed_at=departed_at,
                    distance=getattr(a, "distance", 0) * 0.00062137,
                    strava_id=getattr(a, "id", None),
                    notes=getattr(a, "name", None),
                )
                activities.append(act)
            except Exception as e:
                if debug:
                    print(f"DEBUG: Exception processing activity: {e}")
                continue
        return activities
