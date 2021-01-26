"""
activity_collection.py: representing a service that holds activities
"""

from typing import Protocol
from typing import List
import datetime
import array

from fitler.activity import Activity


class ActivityCollection(Protocol):
    """A standardized object reflecting a fitness activity"""

    def __init__(self, params={}):
        self.activities = []

    def initialize(self) -> bool:
        return True

    def activities(self) -> List[Activity]:
        return self.activities
