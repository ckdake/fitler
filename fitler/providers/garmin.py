"""Garmin provider for Fitler.

This module defines the GarminProvider class, which provides a stub interface
for interacting with Garmin activity data. Currently not implemented.

TODO: implement using https://pypi.org/project/garminconnect/, including adding an auth_garmin.py helper command (like auth_strava.py)
"""

import os
from typing import List, Optional, Dict

from fitler.providers.base import FitnessProvider
from fitler.activity import Activity


class GarminProvider(FitnessProvider):
    """Stub provider for Garmin activities - not yet implemented."""

    def __init__(self):
        """Initialize GarminProvider with environment credentials."""
        self.username = os.environ.get("GARMIN_EMAIL", "")
        self.password = os.environ.get("GARMIN_PASSWORD", "")

    def pull_activities(self, date_filter: str) -> List[Activity]:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def get_gear(self) -> Dict[str, str]:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def create_activity(self, activity: Activity) -> str:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Stub method - not yet implemented."""
        raise NotImplementedError("GarminProvider not yet implemented")
