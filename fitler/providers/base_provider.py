"""Base provider interface for fitness data providers.

This module defines the abstract base class that all provider implementations
should inherit from, ensuring a consistent interface across different fitness
data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class FitnessProvider(ABC):
    """Abstract base class for fitness data providers.

    All providers must implement this interface to ensure consistent
    behavior across different fitness data sources.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the provider with configuration."""
        self.config = config or {}

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""

    @abstractmethod
    def pull_activities(self, date_filter: Optional[str] = None) -> List:
        """
        Pull activities from the provider for a given date filter.
        If date_filter is None, pulls all activities.
        Fetches from provider API/source and persists to database.
        Returns a list of provider-specific activity objects.
        """

    @abstractmethod
    def create_activity(self, activity_data: Dict[str, Any]) -> Any:
        """Create a new activity from activity data. Returns provider-specific activity object."""

    @abstractmethod
    def get_activity_by_id(self, activity_id: str) -> Optional[Any]:
        """Fetch a single activity by its provider-specific ID."""

    @abstractmethod
    def update_activity(self, activity_data: Dict[str, Any]) -> Any:
        """Update an existing activity on the provider."""

    @abstractmethod
    def get_all_gear(self) -> Dict[str, str]:
        """Fetch gear/equipment from the provider, if supported."""

    @abstractmethod
    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Set the gear/equipment for a specific activity on the provider."""
