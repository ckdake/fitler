"""This is the init module for fitler"""

from .activity import Activity

# Providers
from .providers.strava import StravaProvider
from .providers.ridewithgps import RideWithGPSProvider
from .providers.stravajson import StravaJsonProvider
from .providers.spreadsheet import SpreadsheetProvider
from .providers.file import FileProvider
from .providers.garmin import GarminProvider

__version__ = "0.0.1"
__all__ = [
    "Activity",
    "StravaProvider",
    "RideWithGPSProvider",
    "StravaJsonProvider",
    "SpreadsheetProvider",
    "FileProvider",
    "GarminProvider",
]
