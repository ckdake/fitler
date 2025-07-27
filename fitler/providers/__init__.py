"""Fitness service provider integrations for fitler."""

from .spreadsheet import SpreadsheetProvider
from .strava import StravaProvider
from .ridewithgps import RideWithGPSProvider
from .stravajson import StravaJsonProvider
from .garmin import GarminProvider
from .file import FileProvider

__all__ = [
    "SpreadsheetProvider",
    "StravaProvider",
    "RideWithGPSProvider",
    "StravaJsonProvider",
    "GarminProvider",
    "FileProvider",
]
