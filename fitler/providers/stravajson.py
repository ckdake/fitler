"""Strava JSON provider for Fitler.

This module defines the StravaJsonProvider class, which provides an interface
for interacting with locally cached Strava activity data stored as JSON files.
It supports fetching activities from a folder of JSON files, but does not support
uploading, creating, updating, or managing gear.
"""

import glob
import json
from typing import List, Optional, Dict
import dateparser

from fitler.providers.base import FitnessProvider
from fitler.activity import Activity


class StravaJsonProvider(FitnessProvider):
    """Provider for reading Strava activity data from JSON files."""

    def __init__(self, folder: str):
        """Initialize with folder containing JSON files."""
        self.folder = folder

    def pull_activities(self, date_filter: str) -> List[Activity]:
        """Pull activities from JSON files - not yet implemented."""
        raise NotImplementedError(
            "StravaJsonProvider pull_activities not yet implemented"
        )

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Get activity by ID - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support fetching by ID.")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        """Update activity - not supported for JSON files."""
        raise NotImplementedError(
            "StravaJsonProvider does not support updating activities."
        )

    def get_gear(self) -> Dict[str, str]:
        """Get gear - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support gear.")

    def create_activity(self, activity: Activity) -> str:
        """Create activity - not supported for JSON files."""
        raise NotImplementedError(
            "StravaJsonProvider does not support creating activities."
        )

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Set gear - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support setting gear.")


class StravaJsonActivities(FitnessProvider):
    def __init__(self, folder):
        self.folder = folder

    def fetch_activities(self) -> List[Activity]:
        activities = []
        gen = glob.iglob(self.folder)
        for file in gen:
            with open(file) as f:
                data = json.load(f)
                parsed_date = dateparser.parse(data.get("start_date_local"))
                start_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
                activity = Activity(
                    name=data.get("name"),
                    start_date=start_date,
                    start_time=data.get("start_date_local"),
                    distance=data.get("distance", 0) * 0.00062137,
                    strava_id=data.get("id"),
                    notes=data.get("name"),
                )
                activities.append(activity)
        return activities

    def upload_activity(self, activity: Activity) -> str:
        raise NotImplementedError(
            "StravaJsonActivities does not support uploading activities."
        )

    def create_activity(self, activity: Activity) -> str:
        raise NotImplementedError(
            "StravaJsonActivities does not support creating activities."
        )

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        raise NotImplementedError(
            "StravaJsonActivities does not support fetching by ID."
        )

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        raise NotImplementedError(
            "StravaJsonActivities does not support updating activities."
        )

    def get_gear(self) -> Dict[str, str]:
        raise NotImplementedError("StravaJsonActivities does not support gear.")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("StravaJsonActivities does not support setting gear.")
