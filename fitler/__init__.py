"""This is the init module for fitler"""

from .datafiles import ActivityFileCollection, ActivityFile
from .providers.base import Activity

# Providers
from .providers.strava import StravaProvider
from .providers.ridewithgps import RideWithGPSProvider
from .providers.stravajson import StravaJsonActivities
from .providers.spreadsheet import SpreadsheetProvider

__version__ = "0.0.1"
__all__ = [
    "ActivityFileCollection",
    "ActivityFile",
    "Activity",
    "StravaProvider",
    "RideWithGPSProvider",
    "StravaJsonActivities",
    "SpreadsheetProvider",
]
