from fitler.metadata import ActivityMetadata

import dateparser
import glob
import json

class StravaJsonActivities(object):
    def __init__(self, folder):
        self.folder = folder 
        self.activities_metadata = []

    def process(self, limit = -1):
        gen = glob.iglob(self.folder)

        counter = 0
        for file in gen:
            if limit > 0 and counter == limit:
                break
            else:
                counter += 1
                with open(file) as f:
                    data = json.load(f)
                    am_dict = {}
                    am_dict['date'] = dateparser.parse(data["start_date_local"]).strftime("%Y-%m-%d")
                    am_dict['distance'] = data["distance"] * 0.00062137
                    am_dict['strava_id'] = data["id"]
                    am_dict['notes'] = data["name"]
                    am_dict['source'] = "StravaFile"

                    am, created = ActivityMetadata.get_or_create(**am_dict)
                    am.save()
                    self.activities_metadata.append(am)