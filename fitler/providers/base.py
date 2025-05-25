from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class Activity:
    """
    Central representation of an activity in fitler.
    """
    def __init__(
        self,
        source_file: Optional[str] = None,
        source_file_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        location_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        group: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        start_time: Optional[str] = None,
        distance: Optional[float] = None,
        duration: Optional[float] = None,
        tss: Optional[float] = None,
        provider_ids: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.source_file = source_file
        self.source_file_type = source_file_type
        self.name = name
        self.description = description
        self.notes = notes
        self.location_name = location_name
        self.tags = tags or []
        self.group = group or []
        self.start_date = start_date
        self.start_time = start_time
        self.distance = distance
        self.duration = duration
        self.tss = tss
        self.provider_ids = provider_ids or {}
        self.extra = extra or {}

    def to_dict(self):
        return self.__dict__

class FitnessProvider(ABC):
    """
    Abstract base class for all fitness service providers.
    """

    @abstractmethod
    def fetch_activities(self) -> List[Activity]:
        """Fetch and return a list of Activity objects from the provider."""
        pass

    @abstractmethod
    def create_activity(self, activity: Activity) -> str:
        """Create a new activity on the provider. Returns the provider's activity ID."""
        pass

    @abstractmethod
    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Fetch a single activity by its provider-specific ID."""
        pass

    @abstractmethod
    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        """Update an existing activity on the provider."""
        pass

    @abstractmethod
    def get_gear(self) -> Dict[str, str]:
        """Fetch gear/equipment from the provider, if supported."""
        pass

    @abstractmethod
    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Set the gear/equipment for a specific activity on the provider."""
        pass