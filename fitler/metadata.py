import json
from dateutil import parser as dateparser

class ActivityMetadata(object):
    def __init__(self, file = ''):
        self.start_time = ''
        self.original_filename = file.split('/')[-1]
        self.date = ''
        self.activity_type = ''
        self.location_name = ''
        self.city = ''
        self.state = ''
        self.temperature = ''
        self.equipment = ''
        self.duration_hms = ''
        self.distance = ''
        self.max_speed = ''
        self.avg_heart_rate = ''
        self.max_heart_rate = ''
        self.calories = ''
        self.max_elevation = ''
        self.total_elevation_gain = ''
        self.with_names = ''
        self.avg_cadence = ''
        self.strava_id = ''
        self.garmin_id = ''
        self.ridewithgps_id = ''
        self.notes = ''

    def set_start_time(self, datetimestring):
        self.start_time = dateparser.parse(datetimestring).astimezone().replace(microsecond=0).isoformat()
        self.date = dateparser.parse(datetimestring).strftime("%Y-%m-%d")

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)