"""Garmin provider for Fitler.

This module defines the GarminActivities class, which provides a stub interface
for interacting with Garmin activity data.
"""

import os
from typing import List, Optional, Dict

from fitler.providers.base import FitnessProvider
from fitler.activity import Activity


class GarminActivities(FitnessProvider):
    """Stub provider for Garmin activities."""

    def __init__(self):
        """Initialize GarminActivities with environment credentials."""
        self.username = os.environ.get("GARMIN_EMAIL", "")
        self.password = os.environ.get("GARMIN_PASSWORD", "")
        # Add any other required setup here

    def fetch_activities(self) -> List[Activity]:
        """Fetch activities from Garmin (not implemented)."""
        raise NotImplementedError("Garmin fetch_activities not implemented.")

    def create_activity(self, activity: Activity) -> str:
        """Create an activity on Garmin (not implemented)."""
        raise NotImplementedError("Garmin create_activity not implemented.")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Get a specific activity by ID from Garmin (not implemented)."""
        raise NotImplementedError("Garmin get_activity_by_id not implemented.")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        """Update an activity on Garmin (not implemented)."""
        raise NotImplementedError("Garmin update_activity not implemented.")

    def get_gear(self) -> Dict[str, str]:
        """Get gear information from Garmin (not implemented)."""
        raise NotImplementedError("Garmin get_gear not implemented.")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Set gear for an activity on Garmin (not implemented)."""
        raise NotImplementedError("Garmin set_gear not implemented.")
