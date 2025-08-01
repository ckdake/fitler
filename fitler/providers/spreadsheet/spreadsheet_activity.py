"""Spreadsheet-specific activity model."""

from peewee import CharField
from fitler.providers.base_provider_activity import BaseProviderActivity
from fitler.db import db


class SpreadsheetActivity(BaseProviderActivity):
    """Spreadsheet-specific activity data.

    Stores activity data from spreadsheet/CSV files.
    """

    # Spreadsheet-specific ID field (could be row number or custom ID)
    spreadsheet_id = CharField(max_length=50, unique=True, index=True)

    # Spreadsheet-specific fields
    # This might include things like manual notes, custom categories, etc.

    class Meta:
        database = db
        table_name = "spreadsheet_activities"

    @property
    def provider_id(self) -> str:
        """Return the Spreadsheet ID as the provider ID."""
        return str(self.spreadsheet_id) if self.spreadsheet_id else ""

    @provider_id.setter
    def provider_id(self, value: str) -> None:
        """Set the Spreadsheet ID when provider_id is set."""
        self.spreadsheet_id = value
