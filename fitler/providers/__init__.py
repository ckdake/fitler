"""Fitness service provider integrations for fitler."""

from .base import FitnessProvider

from .spreadsheet import SpreadsheetActivities
from .strava import StravaActivities
from .ridewithgps import RideWithGPSActivities

__all__ = [
    "FitnessProvider",
    "LocalSpreadsheetActivities",
    "StravaActivities",
    "RideWithGPSActivities",
]