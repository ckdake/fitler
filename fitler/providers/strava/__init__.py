"""Strava provider module."""

from .strava_provider import StravaProvider

__all__ = ['StravaProvider']

from .strava_provider import StravaProvider
from .strava_activity import StravaActivity

__all__ = ["StravaProvider", "StravaActivity"]
