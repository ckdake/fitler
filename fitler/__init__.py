"""This is the init module for fitler"""

from .datafiles import ActivityFileCollection, ActivityFile
from .metadata import ActivityMetadata

# Providers
from .providers.strava import StravaActivities
from .providers.ridewithgps import RideWithGPSActivities
from .providers.stravajson import StravaJsonActivities
from .providers.spreadsheet import SpreadsheetActivities

__version__ = "0.0.1"
__all__ = [
    "ActivityFileCollection",
    "ActivityFile",
    "ActivityMetadata",
    "StravaActivities",
    "RideWithGPSActivities",
    "StravaJsonActivities",
    "SpreadsheetActivities",
]
