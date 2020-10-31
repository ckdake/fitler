import json
from dateutil import parser as dateparser

class ActivityMetadata(object):
    def __init__(self, file):
        self.start_time = ''
        self.original_filename = file.split('/')[-1]

    def set_start_time(self, datetimestring):
        self.start_time = dateparser.parse(datetimestring).astimezone().replace(microsecond=0).isoformat()

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)