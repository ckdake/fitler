from fitler.metadata import ActivityMetadata

import openpyxl
from pathlib import Path

import json
from dateutil import parser as dateparser

class ActivitySpreadsheet(object):
    def __init__(self, path):
        self.path = path
        self.activities_metadata = []

    def parse(self):
        xlsx_file = Path('ActivityData', self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        col_names = []
        for column in sheet.iter_cols(1, sheet.max_column):
            col_names.append(column[0].value)

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i != 0:
                am = ActivityMetadata()
                am.date = dateparser.parse(str(row[0])).strftime("%Y-%m-%d")
                am.activity_type = row[1]
                am.location_name = row[2]
                am.city = row[3]
                am.state = row[4]
                am.temperature = row[5]
                am.equipment = row[6]
                am.duration_hms = row[7]
                # row[8] is calculated 'duration_h', 
                am.distance = row[9]
                am.max_speed = row[10]
                am.avg_heart_rate = row[11]
                am.calories = row[12]
                am.max_elevation = row[13]
                am.total_elevation_gain = row[14]
                am.with_names = row[15]
                am.avg_heart_rate = row[16]
                am.strava_id = row[17]
                am.garmin_id = row[18]
                am.notes = row[19]
                self.activities_metadata.append(am)
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4) 