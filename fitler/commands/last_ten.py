import json
import os
from pathlib import Path
from fitler.providers.spreadsheet import SpreadsheetActivities
from fitler.providers.strava import StravaActivities
from fitler.providers.ridewithgps import RideWithGPSActivities

CONFIG_PATH = Path("fitler_config.json")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def print_activities(provider_name, activities, id_field):
    print(f"\n{provider_name} (most recent 10):")
    print(f"{'ID':<12} {'Name':<30} {'Date':<12} {'Distance (mi)':>12}")
    print("-" * 70)
    for act in activities:
        act_id = getattr(act, id_field, None)
        name = getattr(act, 'name', None) or getattr(act, 'notes', '')
        date = getattr(act, 'start_date', '')
        if date is None:
            date = ''
        dist = getattr(act, 'distance', 0)
        print(f"{str(act_id):<12} {str(name)[:28]:<30} {str(date):<12} {dist:12.2f}")


def run():
    config = load_config()

    # Spreadsheet
    spreadsheet_path = config.get("spreadsheet_path")
    spreadsheet = SpreadsheetActivities(spreadsheet_path)
    spreadsheet_acts = spreadsheet.fetch_activities()[-10:]
    print_activities("Spreadsheet", spreadsheet_acts, "spreadsheet_id")

    # Strava
    strava_token = os.environ.get("STRAVA_ACCESS_TOKEN")
    if strava_token:
        strava = StravaActivities(strava_token)
        strava_acts = strava.fetch_activities()[-10:]
        print_activities("Strava", strava_acts, "strava_id")
    else:
        print("\nStrava: STRAVA_ACCESS_TOKEN not set in environment, skipping.")

    # RideWithGPS
    for env_var, key in [
        ("RIDEWITHGPS_EMAIL", "ridewithgps_email"),
        ("RIDEWITHGPS_PASSWORD", "ridewithgps_password"),
        ("RIDEWITHGPS_KEY", "ridewithgps_key")
    ]:
        if not os.environ.get(env_var):
            os.environ[env_var] = config.get(key, "")
    try:
        rwgps = RideWithGPSActivities()
        rwgps_acts = rwgps.fetch_activities()[-10:]
        print_activities("RideWithGPS", rwgps_acts, "ridewithgps_id")
    except Exception as e:
        print(f"\nRideWithGPS: Error fetching activities: {e}")