import os
from typing import List, Optional, Dict

from fitler.providers.base import FitnessProvider, Activity


class GarminActivities(FitnessProvider):
    def __init__(self):
        # Placeholder for Garmin authentication/initialization
        self.username = os.environ.get("GARMIN_EMAIL", "")
        self.password = os.environ.get("GARMIN_PASSWORD", "")
        # Add any other required setup here

    def fetch_activities(self) -> List[Activity]:
        raise NotImplementedError("Garmin fetch_activities not implemented.")

    def create_activity(self, activity: Activity) -> str:
        raise NotImplementedError("Garmin create_activity not implemented.")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        raise NotImplementedError("Garmin get_activity_by_id not implemented.")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        raise NotImplementedError("Garmin update_activity not implemented.")

    def get_gear(self) -> Dict[str, str]:
        raise NotImplementedError("Garmin get_gear not implemented.")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("Garmin set_gear not implemented.")
