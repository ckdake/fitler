"""Fitness service provider integrations for fitler."""

from .base import FitnessProvider

from .spreadsheet import SpreadsheetProvider
from .strava import StravaProvider
from .ridewithgps import RideWithGPSProvider

__all__ = [
    "FitnessProvider",
    "SpreadsheetProvider",
    "StravaProvider",
    "RideWithGPSProvider",
]
