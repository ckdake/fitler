from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class Activity:
    """
    Central representation of an activity in fitler.

    All numbers should be in Standard units (miles, Fahrenheit, etc.)
    """

    def __init__(
        self,
        source_file: Optional[str] = None,
        source_file_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        equipment: Optional[str] = None,
        notes: Optional[str] = None,
        location_name: Optional[str] = None,
        activity_type: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        temperature: Optional[float] = None,
        max_speed: Optional[float] = None,
        avg_heart_rate: Optional[float] = None,
        max_heart_rate: Optional[float] = None,
        calories: Optional[float] = None,
        max_elevation: Optional[float] = None,
        total_elevation_gain: Optional[float] = None,
        with_names: Optional[str] = None,
        avg_cadence: Optional[float] = None,
        tags: Optional[List[str]] = None,
        group: Optional[List[str]] = None,
        departed_at: Optional[str] = None,
        distance: Optional[float] = None,
        duration: Optional[float] = None,
        tss: Optional[float] = None,
        strava_id: Optional[str] = None,
        garmin_id: Optional[str] = None,
        ridewithgps_id: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
    ):
        self.source_file = source_file
        self.source_file_type = source_file_type
        self.name = name
        self.description = description
        self.equipment = equipment
        self.notes = notes
        self.location_name = location_name
        self.activity_type = activity_type
        self.city = city
        self.state = state
        self.temperature = temperature
        self.max_speed = max_speed
        self.avg_heart_rate = avg_heart_rate
        self.max_heart_rate = max_heart_rate
        self.calories = calories
        self.max_elevation = max_elevation
        self.total_elevation_gain = total_elevation_gain
        self.with_names = with_names
        self.avg_cadence = avg_cadence
        self.tags = tags or []
        self.group = group or []
        self.departed_at = departed_at
        self.distance = distance
        self.duration = duration
        self.tss = tss
        self.strava_id = strava_id
        self.garmin_id = garmin_id
        self.ridewithgps_id = ridewithgps_id
        self.spreadsheet_id = spreadsheet_id

    def to_dict(self):
        return self.__dict__


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
    def sync_activities(self, date_filter: str) -> List[Activity]:
        """
        Sync activities for a given month filter in YYYY-MM format.
        Returns a list of synced Activity objects.
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
