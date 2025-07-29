"""Fitness service provider integrations for fitler."""

from .spreadsheet.spreadsheet_provider import SpreadsheetProvider
from .strava.strava_provider import StravaProvider
from .ridewithgps.ridewithgps_provider import RideWithGPSProvider
from .stravajson.stravajson_provider import StravaJsonProvider
from .garmin.garmin_provider import GarminProvider
from .file.file_provider import FileProvider

__all__ = [
    "SpreadsheetProvider",
    "StravaProvider",
    "RideWithGPSProvider",
    "StravaJsonProvider",
    "GarminProvider",
    "FileProvider",
]
