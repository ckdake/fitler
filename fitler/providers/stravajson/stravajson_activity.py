"""StravaJson-specific activity model."""

from peewee import CharField
from fitler.providers.base_activity import BaseProviderActivity


class StravaActivity(BaseProviderActivity):
    """Strava-specific activity data.
    
    Stores raw activity data pulled from the Strava API.
    """
    
    # Strava-specific ID field
    strava_id = CharField(max_length=50, unique=True, index=True)
    
    # Strava-specific fields can be added here as needed
    # For example: kudos_count, comment_count, etc.
    
    class Meta:
        database = BaseProviderActivity.Meta.database
        table_name = "strava_activities"
    
    @property
    def provider_id(self) -> str:
        """Return the Strava ID as the provider ID."""
        return str(self.strava_id) if self.strava_id else ""
    
    @provider_id.setter
    def provider_id(self, value: str) -> None:
        """Set the Strava ID when provider_id is set."""
        self.strava_id = value
