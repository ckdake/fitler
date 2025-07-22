from abc import ABC, abstractmethod
from typing import List, Optional, Dict

# Import Activity from the new location
from fitler.activity import Activity


class FitnessProvider(ABC):
    """
    Abstract base class for all fitness service providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    def pull_activities(self, date_filter: str) -> List["Activity"]:
        """
        Pull activities for a given month filter in YYYY-MM format.
        Fetches from provider API/source and persists to database.
        Returns a list of Activity objects.
        """
        pass

    @abstractmethod
    def create_activity(self, activity: Activity) -> str:
        """Create a new activity on the provider. Returns the provider's activity ID."""

    @abstractmethod
    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Fetch a single activity by its provider-specific ID."""

    @abstractmethod
    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        """Update an existing activity on the provider."""

    @abstractmethod
    def get_gear(self) -> Dict[str, str]:
        """Fetch gear/equipment from the provider, if supported."""

    @abstractmethod
    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Set the gear/equipment for a specific activity on the provider."""
