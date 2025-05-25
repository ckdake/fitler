import time
import dateparser
import stravaio  # type: ignore
from typing import List, Optional, Dict

from fitler.providers.base import FitnessProvider, Activity


class StravaActivities(FitnessProvider):
    def __init__(self, token: str):
        self.client = stravaio.StravaIO(access_token=token)

    def fetch_activities(self) -> List[Activity]:
        activities = []
        list_activities = self.client.get_logged_in_athlete_activities()
        for a in list_activities:
            try:
                activity = self.client.get_activity_by_id(a.id)
                activity_dict = activity.to_dict()
                parsed_date = dateparser.parse(activity_dict.get("start_date_local"))
                start_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else None
                act = Activity(
                    name=activity_dict.get("name"),
                    start_date=start_date,
                    start_time=activity_dict.get("start_date_local"),
                    distance=activity_dict.get("distance", 0)
                    * 0.00062137,  # meters to miles
                    provider_ids={"strava": activity_dict.get("id")},
                    notes=activity_dict.get("name"),
                )
                # am_dict['activity_type'] = activity_type
                # am_dict['location_name'] = location_name
                # am_dict['city'] = city  ---> get from start_latlng
                # am_dict['state'] = state  ---> get from start_latlng
                # am_dict['temperature'] = temperature
                # am_dict['equipment'] = equipment
                #     ---> get from gear_id and join
                # am_dict['duration_hms'] = duration_hms
                #     ---> get from elapsed_time in s
                # source data is in meters, convert to miles
                # am_dict['max_speed'] = max_speed
                #     --->  convert from m/s to mph
                # am_dict['avg_heart_rate'] = avg_heart_rate
                #  am_dict['calories'] = calories
                # am_dict['max_elevation'] = max_elevation
                # am_dict['total_elevation_gain'] = total_elevation_gain
                # am_dict['with_names'] = with_names
                # am_dict['avg_heart_rate'] = avg_heart_rate
                activities.append(act)
                time.sleep(2)
            except Exception as e:
                print("Exception fetching Strava Activity:", e)
        return activities

    def create_activity(self, activity: Activity) -> str:
        # Implement upload logic if needed
        raise NotImplementedError("Strava create_activity not implemented.")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        try:
            activity = self.client.get_activity_by_id(activity_id)
            activity_dict = activity.to_dict()
            return Activity(
                name=activity_dict.get("name"),
                start_time=activity_dict.get("start_date_local"),
                distance=activity_dict.get("distance", 0) * 0.00062137,
                provider_ids={"strava": activity_dict.get("id")},
                notes=activity_dict.get("name"),
            )
        except Exception as e:
            print("Exception fetching Strava Activity by ID:", e)
            return None

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        # Not implemented for Strava
        raise NotImplementedError("Strava update_activity not implemented.")

    def get_gear(self) -> Dict[str, str]:
        # Not implemented for Strava
        return {}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        # Not implemented for Strava
        raise NotImplementedError("Strava set_gear not implemented.")
