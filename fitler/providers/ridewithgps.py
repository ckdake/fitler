import os
import dateparser
import ridewithgps  # type: ignore
import requests
from typing import List, Optional, Dict

from fitler.providers.base import FitnessProvider, Activity


class RideWithGPSActivities(FitnessProvider):
    def __init__(self):
        self.client = ridewithgps.RideWithGPS()
        self.username = os.environ["RIDEWITHGPS_EMAIL"]
        self.password = os.environ["RIDEWITHGPS_PASSWORD"]
        self.apikey = os.environ["RIDEWITHGPS_KEY"]

        auth = self.client.call(
            "/users/current.json",
            {
                "email": self.username,
                "password": self.password,
                "apikey": self.apikey,
                "version": 2,
            },
        )
        self.userid = auth["user"]["id"]
        self.auth_token = auth["user"]["auth_token"]

    def fetch_activities(self) -> List[Activity]:
        activities = []
        gear = self.get_gear()
        api_activities = self.client.call(
            f"/users/{self.userid}/trips.json",
            {
                "offset": 0,
                "limit": 10000,
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
            },
        )["results"]
        for a in api_activities:
            try:
                departed_at = a.get("departed_at")
                parsed_date = dateparser.parse(departed_at)
                start_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
                act = Activity(
                    start_time=departed_at,
                    distance=a.get("distance", 0) * 0.00062137,  # meters to miles
                    start_date=start_date,
                    provider_ids={"ridewithgps": a.get("id")},
                    notes=a.get("name"),
                    equipment=gear[a["gear_id"]] if a.get("gear_id") else "",
                    # Add more fields as needed
                )
                activities.append(act)
            except Exception as e:
                print("Exception fetching RideWithGPS Activity:", e)
        return activities

    def create_activity(self, activity: Activity) -> str:
        # Implements create_trip (upload a file to RideWithGPS)
        if not activity.source_file:
            raise ValueError("No source file provided for activity upload.")
        with open(activity.source_file, "rb") as file_obj:
            response = requests.post(
                "https://ridewithgps.com/trips.json",
                files={"file": file_obj},
                data={
                    "apikey": self.apikey,
                    "version": 2,
                    "auth_token": self.auth_token,
                },
            )
        if response.status_code == 200:
            trip = response.json().get("trip", {})
            return str(trip.get("id"))
        else:
            raise Exception(f"Failed to create trip: {response.text}")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        # Not implemented
        raise NotImplementedError("RideWithGPS get_activity_by_id not implemented.")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        # Implements set_trip_name pattern: update the name field of a trip/activity
        if not activity.name:
            raise ValueError("No name provided for activity update.")
        response = self.client.call(
            f"/trips/{activity_id}.json",
            {
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
                "name": activity.name,
            },
            method="PUT",
        )
        return response.get("trip", {}).get("name") == activity.name

    def get_gear(self) -> Dict[str, str]:
        gear = {}
        gear_results = self.client.call(
            f"/users/{self.userid}/gear.json",
            {
                "offset": 0,
                "limit": 100,
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
            },
        )["results"]
        for g in gear_results:
            gear[g["id"]] = g["nickname"]
        return gear

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        # Implements set_trip_gear: set the gear for a trip/activity
        response = self.client.call(
            f"/trips/{activity_id}.json",
            {
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
                "gear_id": gear_id,
            },
            method="PUT",
        )
        return response.get("trip", {}).get("gear_id") == gear_id
