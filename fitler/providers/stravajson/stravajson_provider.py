"""Strava JSON provider for Fitler.

This module defines the StravaJsonProvider class, which provides an interface
for interacting with locally cached Strava activity data stored as JSON files.
It supports fetching activities from a folder of JSON files, but does not support
uploading, creating, updating, or managing gear.
"""

import glob
import json
from typing import List, Optional, Dict, Any
import dateparser

from fitler.providers.base_provider import FitnessProvider
from fitler.providers.stravajson.stravajson_activity import StravaJsonActivity


class StravaJsonProvider(FitnessProvider):
    """Provider for reading Strava activity data from JSON files."""

    def __init__(self, folder: str, config: Optional[Dict[str, Any]] = None):
        """Initialize with folder containing JSON files."""
        super().__init__(config)
        self.folder = folder

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "stravajson"

    def pull_activities(
        self, date_filter: Optional[str] = None
    ) -> List[StravaJsonActivity]:
        """Pull activities from JSON files - not yet implemented."""
        print("StravaJSON provider: pulling activities not implemented yet")
        return []

    def get_activity_by_id(self, activity_id: str) -> Optional[StravaJsonActivity]:
        """Get activity by ID - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support fetching by ID.")

    def update_activity(self, activity_id: str, activity: StravaJsonActivity) -> bool:
        """Update activity - not supported for JSON files."""
        raise NotImplementedError(
            "StravaJsonProvider does not support updating activities."
        )

    def get_gear(self) -> Dict[str, str]:
        """Get gear - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support gear.")

    def create_activity(self, activity: StravaJsonActivity) -> str:
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

    def fetch_activities(self) -> List[StravaJsonActivity]:
        activities = []
        gen = glob.iglob(self.folder)
        for file in gen:
            with open(file) as f:
                data = json.load(f)
                parsed_date = dateparser.parse(data.get("start_date_local"))
                start_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
                activity = StravaJsonActivity(
                    name=data.get("name"),
                    start_date=start_date,
                    start_time=data.get("start_date_local"),
                    distance=data.get("distance", 0) * 0.00062137,
                    strava_id=data.get("id"),
                    notes=data.get("name"),
                )
                activities.append(activity)
        return activities

    def upload_activity(self, activity: StravaJsonActivity) -> str:
        raise NotImplementedError(
            "StravaJsonActivities does not support uploading activities."
        )

    def create_activity(self, activity: StravaJsonActivity) -> str:
        raise NotImplementedError(
            "StravaJsonActivities does not support creating activities."
        )

    def get_activity_by_id(self, activity_id: str) -> Optional[StravaJsonActivity]:
        raise NotImplementedError(
            "StravaJsonActivities does not support fetching by ID."
        )

    def update_activity(self, activity_id: str, activity: StravaJsonActivity) -> bool:
        raise NotImplementedError(
            "StravaJsonActivities does not support updating activities."
        )

    def get_gear(self) -> Dict[str, str]:
        raise NotImplementedError("StravaJsonActivities does not support gear.")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("StravaJsonActivities does not support setting gear.")
