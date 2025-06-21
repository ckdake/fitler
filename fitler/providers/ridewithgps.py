"""RideWithGPS provider for Fitler.

This module defines the RideWithGPSActivities class, which provides an interface
for interacting with RideWithGPS activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
from typing import List, Optional, Dict
import dateparser
from ridewithgps import RideWithGPS

from fitler.providers.base import FitnessProvider, Activity


class RideWithGPSActivities(FitnessProvider):
    def __init__(self):
        self.username = os.environ["RIDEWITHGPS_EMAIL"]
        self.password = os.environ["RIDEWITHGPS_PASSWORD"]
        self.apikey = os.environ["RIDEWITHGPS_KEY"]

        self.client = RideWithGPS(apikey=self.apikey, cache=True)

        user_info = self.client.authenticate(self.username, self.password)
        self.userid = user_info.get("id")

    def fetch_activities(self) -> List[Activity]:
        activities = []
        trips = self.client.list(f"/users/{self.userid}/trips")
        gear = self.get_gear()
        for trip in trips:
            try:
                departed_at = trip.get("departed_at")
                parsed_date = dateparser.parse(departed_at)
                start_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
                act = Activity(
                    start_time=departed_at,
                    distance=trip.get("distance", 0) * 0.00062137,  # meters to miles
                    start_date=start_date,
                    ridewithgps_id=trip.get("id"),
                    notes=trip.get("name"),
                    equipment=(
                        gear.get(trip.get("gear_id"), "") if trip.get("gear_id") else ""
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
            # According to the ridewithgps package, use put for uploads
            trip = self.client.put(path="/trips", files={"file": file_obj})
        return str(trip.get("id"))

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        trip = self.client.get(path=f"/trips/{activity_id}")
        if not trip:
            return None
        gear = self.get_gear()
        departed_at = trip.get("departed_at")
        parsed_date = dateparser.parse(departed_at)
        start_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
        return Activity(
            start_time=departed_at,
            distance=trip.get("distance", 0) * 0.00062137,
            start_date=start_date,
            ridewithgps_id=trip.get("id"),
            notes=trip.get("name"),
            equipment=gear.get(trip.get("gear_id"), "") if trip.get("gear_id") else "",
        )

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        if not activity.name:
            raise ValueError("No name provided for activity update.")
        updated_trip = self.client.put(
            path=f"/trips/{activity_id}", params={"name": activity.name}
        )
        return updated_trip.get("name") == activity.name

    def get_gear(self) -> Dict[str, str]:
        gear = {}
        gear_list = self.client.list(path=f"/users/{self.userid}/gear")
        for g in gear_list:
            gear[g["id"]] = g.get("nickname", "")
        return gear

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        updated_trip = self.client.put(
            path=f"/trips/{activity_id}", param={"gear_id": gear_id}
        )
        return updated_trip.get("gear_id") == gear_id
