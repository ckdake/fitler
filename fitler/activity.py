"""
activity.py: The core building block of fitler, an activity interface
"""

from typing import Protocol
from typing import List
import datetime
import array


class Activity(Protocol):
    """A standardized object reflecting a fitness activity"""

    def __init__(self, params={}):
        return

    def name(self) -> str:
        return ""

    def location_name(self) -> str:
        return ""

    def location_city(self) -> str:
        return ""

    def location_state(self) -> str:
        return ""

    def notes(self) -> str:
        return ""

    def with_names(self) -> List[str]:
        return list()

    def average_temperature_f(self) -> int:
        return 0

    def min_temperature_f(self) -> int:
        return 0

    def max_temperature_f(self) -> int:
        return 0

    def strava_id(self) -> int:
        return 0

    def garmin_id(self) -> int:
        return 0

    def source_sourcename(self) -> str:
        """ e.g. strava """
        return ""

    def source_id(self) -> int:
        """ e.g. strava_id from strava"""
        return -1

    def source_athelete_id(self) -> int:
        """ e.g. athelete_id from strava"""
        return -1

    def distance_meters(self) -> int:
        return -1

    def moving_time_seconds(self) -> int:
        return -1

    def elapsed_time_seconds(self) -> int:
        return -1

    def total_elevation_gain_meters(self) -> int:
        return -1

    def elev_high_meters(self) -> int:
        return -1

    def elev_low_meters(self) -> int:
        return -1

    def activity_type(self) -> str:
        return ""

    def start_date_datetime(self) -> datetime:
        return ""

    def start_date_local_datetime(self) -> datetime:
        return ""

    def timezone(self) -> str:
        return ""

    def start_latlng(self) -> List[float]:
        return []

    def end_latlng(self) -> List[float]:
        return []

    def trainer(self) -> bool:
        return False

    def commute(self) -> bool:
        return False

    def manual(self) -> bool:
        return False

    def private(self) -> bool:
        return False

    def average_speed_meters_second(self) -> float:
        return 0

    def max_speed_meters_second(self) -> float:
        return 0

    def gear_name(self) -> str:
        return ""

    def average_cadence(self) -> int:
        return 0

    def max_cadence(self) -> int:
        return 0

    def power_kj(self) -> float:
        return 0

    def has_heartrate(self) -> bool:
        return False

    def average_heartrate(self) -> int:
        return 0

    def max_heartrate(self) -> int:
        return 0

    def power_average_watts(self) -> float:
        return 0

    def device_watts(self) -> bool:
        return False

    def max_watts(self) -> float:
        return 0

    def weighted_average_watts(self) -> int:
        return 0

    def description(self) -> str:
        return ""

    def calories(self) -> float:
        return 0

    def device_name(self) -> str:
        return ""
