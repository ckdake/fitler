"""Handles locally cached Strava JSON files as a provider."""
from fitler.providers.base import FitnessProvider, Activity

import dateparser
import glob
import json
from typing import List, Optional, Dict, Any

class StravaJsonActivities(FitnessProvider):
    def __init__(self, folder):
        self.folder = folder

    def fetch_activities(self) -> List[Activity]:
        activities = []
        gen = glob.iglob(self.folder)
        for file in gen:
            with open(file) as f:
                data = json.load(f)
                activity = Activity(
                    name=data.get("name"),
                    start_date=dateparser.parse(data["start_date_local"]).strftime("%Y-%m-%d"),
                    start_time=data.get("start_date_local"),
                    distance=data.get("distance", 0) * 0.00062137,
                    provider_ids={"strava": data.get("id")},
                    notes=data.get("name"),
                    extra=data,
                )
                activities.append(activity)
        return activities

    def upload_activity(self, activity: Activity) -> str:
        raise NotImplementedError("StravaJsonActivities does not support uploading activities.")

    def create_activity(self, activity: Activity) -> str:
        raise NotImplementedError("StravaJsonActivities does not support creating activities.")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        raise NotImplementedError("StravaJsonActivities does not support fetching by ID.")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        raise NotImplementedError("StravaJsonActivities does not support updating activities.")

    def get_gear(self) -> Dict[str, str]:
        raise NotImplementedError("StravaJsonActivities does not support gear.")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("StravaJsonActivities does not support setting gear.")