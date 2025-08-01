"""This is the init module for fitler"""

# Providers
from .providers.strava import StravaProvider
from .providers.ridewithgps import RideWithGPSProvider
from .providers.stravajson import StravaJsonProvider
from .providers.spreadsheet import SpreadsheetProvider
from .providers.file import FileProvider
from .providers.garmin import GarminProvider

__version__ = "0.0.1"
__all__ = [
    "StravaProvider",
    "RideWithGPSProvider",
    "StravaJsonProvider",
    "SpreadsheetProvider",
    "FileProvider",
    "GarminProvider",
]
