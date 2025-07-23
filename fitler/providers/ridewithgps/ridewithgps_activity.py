"""RideWithGPS-specific activity model."""

from peewee import CharField
from fitler.providers.base_activity import BaseProviderActivity
from fitler.database import db


class RideWithGPSActivity(BaseProviderActivity):
    """RideWithGPS-specific activity data.

    Stores raw activity data pulled from the RideWithGPS API.
    """

    # RideWithGPS-specific ID field
    ridewithgps_id = CharField(max_length=50, unique=True, index=True)

    # RideWithGPS-specific fields can be added here as needed
    # For example: visibility, route_id, etc.

    class Meta:
        database = db
        table_name = "ridewithgps_activities"

    @property
    def provider_id(self) -> str:
        """Return the RideWithGPS ID as the provider ID."""
        return str(self.ridewithgps_id) if self.ridewithgps_id else ""

    @provider_id.setter
    def provider_id(self, value: str) -> None:
        """Set the RideWithGPS ID when provider_id is set."""
        self.ridewithgps_id = value
