from fitler.metadata import ActivityMetadata

import dateparser
import stravaio
import os
import time

class StravaActivities(object):

    def __init__(self, token):
        self.activities_metadata = []
        self.client = stravaio.StravaIO(access_token=token)
    
    def process(self):
        # TODO: how to load in the stuff stored locally? 

        list_activitites = self.client.get_logged_in_athlete_activities() #after='last week')
        for a in list_activitites:
            try:
                activity = self.client.get_activity_by_id(a.id)
                activity.store_locally()
                activity_dict = activity.to_dict()

                am_dict = {}

                am_dict['date'] = dateparser.parse(activity_dict["start_date_local"]).strftime("%Y-%m-%d")
                # am_dict['activity_type'] = activity_type
                # am_dict['location_name'] = location_name
                # am_dict['city'] = city  ---> get from start_latlng
                # am_dict['state'] = state  ---> get from start_latlng
                # am_dict['temperature'] = temperature
                # am_dict['equipment'] = equipment ---> get from gear_id and join
                # am_dict['duration_hms'] = duration_hms  ---> get from elapsed_time in s
                am_dict['distance'] = activity_dict["distance"] * 0.00062137
                # am_dict['max_speed'] = max_speed  -->  convert from m/s to mph
                # am_dict['avg_heart_rate'] = avg_heart_rate
                #  am_dict['calories'] = calories
                # am_dict['max_elevation'] = max_elevation
                # am_dict['total_elevation_gain'] = total_elevation_gain
                # am_dict['with_names'] = with_names
                # am_dict['avg_heart_rate'] = avg_heart_rate
                am_dict['strava_id'] = activity_dict["id"]
                # if garmin_id := row[18]: am_dict['garmin_id'] = garmin_id
                am_dict['notes'] = activity_dict["name"]
                am_dict['source'] = "Strava"

                am, created = ActivityMetadata.get_or_create(**am_dict)
                am.save()
                self.activities_metadata.append(am)
                time.sleep(2)
            except Exception as e:
                # TODO: fix ValueError: Invalid value for `activity_type` (Hike), must be one of ['Ride', 'Run']
                print(e)

        # TODO: destroy the client somehow

class RideWithGPSActivities(object):
    # 1. get an auth token using os.environ['RIDEWITHGPS_KEY'] and username/password
    # 2. pull activities

    def __init__(self, token):
        self.activities_metadata = []
        self.client = []
    
    def process(self):
        for a in []:
            am_dict = {}
            am_dict['source'] = "Spreadsheet"
            am, created = ActivityMetadata.get_or_create(**am_dict)
            am.save()
            self.activities_metadata.append(am)