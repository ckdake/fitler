import json
import os
import logging
import datetime
from pathlib import Path
from fitler.providers.spreadsheet import SpreadsheetActivities
from fitler.providers.strava import StravaActivities
from fitler.providers.ridewithgps import RideWithGPSActivities

CONFIG_PATH = Path("fitler_config.json")

def load_config():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    if "debug" not in config:
        config["debug"] = False
    return config

def print_activities(provider_name, activities, id_field, home_tz):
    print(f"\n{provider_name} (for selected month):")
    print(f"{'ID':<12} {'Name':<30} {'Raw Timestamp':<12} {'Local Time':<19} {'Distance (mi)':>12}")
    print("-" * 85)
    for act in activities:
        act_id = getattr(act, id_field, None)
        name = getattr(act, 'name', None) or getattr(act, 'notes', '')
        departed_at = getattr(act, 'departed_at', None)
        # Convert UTC timestamp to local time for display
        date_str = ''
        if departed_at:
            try:
                utc = datetime.datetime.fromtimestamp(int(departed_at), datetime.timezone.utc)
                local = utc.astimezone(home_tz)
                date_str = f"{local.strftime('%Y-%m-%d %H:%M')} {local.tzname()}"
            except:
                date_str = 'invalid'
        dist = getattr(act, 'distance', 0)
        print(f"{str(act_id):<12} {str(name)[:28]:<30} {str(departed_at):<12} {str(date_str):<19} {dist:12.2f}")

def run(year_month):
    config = load_config()
    # Get home timezone once
    from zoneinfo import ZoneInfo
    home_tz = ZoneInfo(config.get('home_timezone', 'US/Eastern'))

    # Convert year_month (YYYY-MM) to start/end timestamps in UTC
    year, month = map(int, year_month.split('-'))
    # Use home timezone for local times
    start_local = datetime.datetime(year, month, 1, tzinfo=home_tz)
    start_utc = start_local.astimezone(datetime.timezone.utc)
    # Get end of month in local time
    if month == 12:
        end_local = datetime.datetime(year + 1, 1, 1, tzinfo=home_tz)
    else:
        end_local = datetime.datetime(year, month + 1, 1, tzinfo=home_tz)
    end_utc = end_local.astimezone(datetime.timezone.utc)

    config = load_config()
    if config.get("debug", False):
        os.environ["STRAVALIB_DEBUG"] = "1"
        logging.basicConfig(level=logging.DEBUG, force=True)
    else:
        logging.basicConfig(level=logging.WARNING, force=True)

    spreadsheet_path = config.get("spreadsheet_path")
    spreadsheet = SpreadsheetActivities(spreadsheet_path)
    spreadsheet_acts = spreadsheet.fetch_activities_for_month(year_month)
    print_activities("Spreadsheet", spreadsheet_acts, "spreadsheet_id", home_tz)

    strava_token = os.environ.get("STRAVA_ACCESS_TOKEN")
    strava_refresh = os.environ.get("STRAVA_REFRESH_TOKEN")
    strava_client_id = os.environ.get("STRAVA_CLIENT_ID")
    strava_client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
    strava_token_expires = os.environ.get("STRAVA_TOKEN_EXPIRES")
    if strava_token:
        strava = StravaActivities(
            strava_token,
            refresh_token=strava_refresh,
            client_id=strava_client_id,
            client_secret=strava_client_secret,
            token_expires=strava_token_expires
        )
        strava_acts = strava.fetch_activities_for_month(year_month)
        print_activities("Strava", strava_acts, "strava_id", home_tz)
    else:
        print("\nStrava: STRAVA_ACCESS_TOKEN not set in environment, skipping.")

    for env_var, key in [
        ("RIDEWITHGPS_EMAIL", "ridewithgps_email"),
        ("RIDEWITHGPS_PASSWORD", "ridewithgps_password"),
        ("RIDEWITHGPS_KEY", "ridewithgps_key")
    ]:
        if not os.environ.get(env_var):
            os.environ[env_var] = config.get(key, "")
    try:
        rwgps = RideWithGPSActivities()
        rwgps_acts = rwgps.fetch_activities()
        # Filter to activities within our UTC time window
        filtered_acts = []
        for act in rwgps_acts:
            departed_at = getattr(act, 'departed_at', None)
            if departed_at:
                ts = int(departed_at)
                if start_utc.timestamp() <= ts < end_utc.timestamp():
                    filtered_acts.append(act)
        print_activities("RideWithGPS", filtered_acts, "ridewithgps_id", home_tz)
    except Exception as e:
        print(f"\nRideWithGPS: Error fetching activities: {e}")
