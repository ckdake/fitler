"""
spreadsheet_activity.py: an activity from a spreadsheet
"""

import datetime
import time
import array
from dateutil import parser as dateparser

from fitler.activity import Activity


class SpreadsheetActivity(Activity):
    """A row in CK's crazy spreadsheet, as an Activity"""

    def __init__(self, row=None, id=None):
        self.start_date_datetime = dateparser.parse(str(row[0])).strftime("%Y-%m-%d")
        if activity_type := row[1]:
            self.activity_type = activity_type
        if location_name := row[2]:
            self.location_name = location_name
        if location_city := row[3]:
            self.location_city = location_city
        if location_state := row[4]:
            self.location_state = location_state
        if average_temperature_f := row[5]:
            self.average_temperature_f = average_temperature_f
        if gear_name := row[6]:
            self.gear_name = gear_name
        if elapsed_time_hms := row[7]:
            if type(elapsed_time_hms) is datetime.time:
                elapsed_time_hms = elapsed_time_hms.strftime("%H:%M:%S")
            if type(elapsed_time_hms) is datetime.datetime:
                elapsed_time_hms = elapsed_time_hms.strftime("%H:%M:%S")
            self.elapsed_time_seconds = sum(
                int(x) * 60 ** i
                for i, x in enumerate(reversed(elapsed_time_hms.split(":")))
            )
        # row[8] is calculated 'duration_h',
        if distance_miles := row[9]:
            self.distance_meters = distance_miles * 1609.344
        if max_speed_mph := row[10]:
            self.max_speed_meters_second = max_speed_mph * 0.00027777777777778
        if average_heartrate := row[11]:
            self.average_heartrate = average_heartrate
        if max_heartrate := row[12]:
            self.max_heartrate = max_heartrate
        if calories := row[13]:
            self.calories = calories
        if max_elevation_feet := row[14]:
            self.max_elevation_meters = max_elevation_feet * 0.3048
        if total_elevation_gain_feet := row[15]:
            self.total_elevation_gain_meters = total_elevation_gain_feet * 0.3048
        if with_names := row[16]:
            self.with_names = with_names.split(";")
        if average_cadence := row[17]:
            self.average_cadence = average_cadence
        if strava_id := row[18]:
            self.strava_id = strava_id
        if garmin_id := row[19]:
            self.garmin_id = garmin_id.split("/")[-1]
        if description := row[20]:
            self.description = description

        self.source_id = id

    def name(self) -> str:
        return self.name

    def source_sourcename(self) -> str:
        return "Spreadsheet"

    def source_id(self) -> int:
        return self.source_id

    def distance_meters(self) -> int:
        return self.distance_meters

    def elapsed_time_seconds(self) -> int:
        return self.elapsed_time_seconds

    def total_elevation_gain_meters(self) -> int:
        return self.total_elevation_gain_meters

    def activity_type(self) -> str:
        return self.activity_type

    def start_date_datetime(self) -> datetime:
        return self.start_date_datetime

    def trainer(self) -> bool:
        return self.name == "Virtual"

    def commute(self) -> bool:
        return self.name == "Commute"

    def average_speed_meters_second(self) -> float:
        return self.average_speed_meters_second

    def max_speed_meters_second(self) -> float:
        return self.max_speed_meters_second

    def gear_name(self) -> str:
        return self.gear_name

    def description(self) -> str:
        return self.description

    def calories(self) -> float:
        return self.calories
