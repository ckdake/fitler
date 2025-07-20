"""RideWithGPS provider for Fitler.

This module defines the RideWithGPSActivities class, which provides an interface
for interacting with RideWithGPS activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
from typing import List, Optional, Dict
import dateparser
from pyrwgps import RideWithGPS
import datetime

from fitler.providers.base import FitnessProvider, Activity


class RideWithGPSActivities(FitnessProvider):
    def __init__(self):
        self.username = os.environ["RIDEWITHGPS_EMAIL"]
        self.password = os.environ["RIDEWITHGPS_PASSWORD"]
        self.apikey = os.environ["RIDEWITHGPS_KEY"]

        self.client = RideWithGPS(apikey=self.apikey, cache=True)

        user_info = self.client.authenticate(self.username, self.password)
        self.userid = getattr(user_info, "id", None)

    def _parse_ridewithgps_datetime(self, dt_val):
        # RideWithGPS provides datetime strings in ISO8601 format with timezone
        # e.g. '2025-01-02T19:55:14-05:00'
        from dateutil import parser as dateparser
        if not dt_val:
            return None
        try:
            # Parse the ISO8601 string which includes timezone
            dt = dateparser.parse(str(dt_val))
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
                    distance=getattr(trip, "distance", 0) * 0.00062137,  # meters to miles
                    ridewithgps_id=getattr(trip, "id", None),
                    notes=getattr(trip, "name", None),
                    equipment=(
                        gear.get(gear_id_str, "") if gear_id_str else ""
                    ),
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
        return hasattr(updated_trip, "trip") and getattr(updated_trip.trip, "name", None) == activity.name

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
        return hasattr(updated_trip, "trip") and getattr(updated_trip.trip, "gear_id", None) == gear_id

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
                except:
                    continue
        return filtered
