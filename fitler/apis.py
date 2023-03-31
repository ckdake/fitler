from fitler.metadata import ActivityMetadata

import dateparser
import stravaio
import os
import time
import ridewithgps
import urllib.parse
import requests
from pprint import pprint

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
                am_dict['distance'] = activity_dict["distance"] * 0.00062137 # source data is in meters, convert to miles
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
                print('Exception Saving Strava Activity:', e)

        # TODO: destroy the client somehow

class RideWithGPSActivities(object):
    def __init__(self):
        self.activities_metadata = []
        self.client = ridewithgps.RideWithGPS()

        self.username = os.environ['RIDEWITHGPS_EMAIL']
        self.password = os.environ['RIDEWITHGPS_PASSWORD']
        self.apikey   = os.environ['RIDEWITHGPS_KEY']

        auth = self.client.call(
            "/users/current.json", 
            {"email": self.username, "password": self.password, "apikey": self.apikey, "version": 2}
        )

        self.userid =  auth['user']['id']
        self.auth_token = auth['user']['auth_token']

    def set_trip_gear(self, trip_id, gear_id):
        r = requests.put(
            "https://ridewithgps.com/trips/{0}.json".format(trip_id),
            json = {
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
                "trip": {
                    "gear_id": gear_id
                }
            }
        )
    
    def set_trip_name(self, trip_id, name):
        r = requests.put(
            "https://ridewithgps.com/trips/{0}.json".format(trip_id),
            json = {
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
                "trip": {
                    "name": name
                }
            }
        )

    def create_trip(self, file_path):
        r = requests.post(
            "https://ridewithgps.com/trips.json",
            files = {
                'file': open(file_path, 'rb')
            },
            data = {
                "apikey": self.apikey,
                "version": 2,
                "auth_token": self.auth_token,
            }
        )

    def get_gear(self):
        gear = {}
        gear_results = self.client.call(
            "/users/{0}/gear.json".format(self.userid),
            {"offset": 0, "limit": 100, "apikey": self.apikey, "version": 2, "auth_token": self.auth_token}
        )["results"]
        for g in gear_results:
            gear[g["id"]] = g["nickname"]
        return gear

    def process(self):
        gear = self.get_gear()

        activities = self.client.call(
            "/users/{0}/trips.json".format(self.userid),
            {"offset": 0, "limit": 10000, "apikey": self.apikey, "version": 2, "auth_token": self.auth_token}
        )["results"]
        for a in activities:
            try:
                am_dict = {}
                
                am_dict['date'] = dateparser.parse(a["departed_at"]).strftime("%Y-%m-%d")
                am_dict['distance'] = a["distance"] * 0.00062137 # source data is in meters, convert to miles
                am_dict['equipment'] = gear[a["gear_id"]] if a["gear_id"] else ""
                am_dict['ridewithgps_id'] = a["id"]
                am_dict['notes'] = a["name"]

                am_dict['source'] = "RideWithGPS"

                am, created = ActivityMetadata.get_or_create(**am_dict)
                am.save()
                
                self.activities_metadata.append(am)

            except Exception as e:
                print('Exception Saving RideWithGPS Activity:', e) 
