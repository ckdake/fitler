"""Strava JSON provider for Fitler.

This module defines the StravaJsonProvider class, which provides an interface
for interacting with locally cached Strava activity data stored as JSON files.
It supports fetching activities from a folder of JSON files, but does not support
uploading, creating, updating, or managing gear.
"""

from typing import List, Optional, Dict, Any

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

    def get_all_gear(self) -> Dict[str, str]:
        """Get gear - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support gear.")

    def create_activity(self, activity: StravaJsonActivity) -> str:
        """Create activity - not supported for JSON files."""
        raise NotImplementedError(
            "StravaJsonProvider does not support creating activities."
        )

    def set_gear(self, gear_name: str, activity_id: str) -> bool:
        """Set gear - not supported for JSON files."""
        raise NotImplementedError("StravaJsonProvider does not support setting gear.")
