import os
import json
from pathlib import Path
from fitler.providers.spreadsheet import SpreadsheetActivities
from fitler.providers.strava import StravaActivities
from fitler.providers.ridewithgps import RideWithGPSActivities
# from fitler.providers.garmin import GarminActivities  # Uncomment if implemented
from datetime import datetime, timezone
from collections import defaultdict
from tabulate import tabulate

CONFIG_PATH = Path("fitler_config.json")

# ANSI color codes for terminal output
green_bg = '\033[42m'
yellow_bg = '\033[43m'
reset = '\033[0m'

def load_config():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    if "debug" not in config:
        config["debug"] = False
    return config

def color_id(id_val, exists):
    if exists:
        return f"{green_bg}{id_val}{reset}"
    else:
        return f"{yellow_bg}TBD{reset}"

def run(year_month):
    config = load_config()
    # Get home timezone from config
    from zoneinfo import ZoneInfo
    home_tz = ZoneInfo(config.get('home_timezone', 'US/Eastern'))

    # Load activities from all providers
    spreadsheet_path = config.get("spreadsheet_path")
    spreadsheet = SpreadsheetActivities(spreadsheet_path)
    spreadsheet_acts = spreadsheet.fetch_activities_for_month(year_month)
    strava_token = os.environ.get("STRAVA_ACCESS_TOKEN")
    strava_refresh = os.environ.get("STRAVA_REFRESH_TOKEN")
    strava_client_id = os.environ.get("STRAVA_CLIENT_ID")
    strava_client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
    strava_token_expires = os.environ.get("STRAVA_TOKEN_EXPIRES")
    strava_acts = []
    if strava_token:
        strava = StravaActivities(
            strava_token,
            refresh_token=strava_refresh,
            client_id=strava_client_id,
            client_secret=strava_client_secret,
            token_expires=strava_token_expires
        )
        strava_acts = strava.fetch_activities_for_month(year_month)
    # garmin_acts = GarminActivities().fetch_activities_for_month(year_month)  # Uncomment if implemented
    garmin_acts = []  # Placeholder
    ridewithgps_acts = []

    for env_var, key in [
        ("RIDEWITHGPS_EMAIL", "ridewithgps_email"),
        ("RIDEWITHGPS_PASSWORD", "ridewithgps_password"),
        ("RIDEWITHGPS_KEY", "ridewithgps_key")
    ]:
        if not os.environ.get(env_var):
            os.environ[env_var] = config.get(key, "")
    try:
        ridewithgps = RideWithGPSActivities()
        ridewithgps_acts = ridewithgps.fetch_activities_for_month(year_month)
    except Exception as e:
        print(f"\nRideWithGPS: Error fetching activities: {e}")

    # Build a list of all activities by date/distance for matching
    all_acts = []
    for act in spreadsheet_acts:
        ts = int(getattr(act, 'departed_at', 0) or 0)
        all_acts.append({
            'provider': 'spreadsheet',
            'id': getattr(act, 'spreadsheet_id', None),
            'timestamp': ts,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })
    for act in strava_acts:
        ts = int(getattr(act, 'departed_at', 0) or 0)
        all_acts.append({
            'provider': 'strava',
            'id': getattr(act, 'strava_id', None),
            'timestamp': ts,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })
    for act in garmin_acts:
        ts = int(getattr(act, 'departed_at', 0) or 0)
        all_acts.append({
            'provider': 'garmin',
            'id': getattr(act, 'garmin_id', None),
            'timestamp': ts,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })
    for act in ridewithgps_acts:
        ts = int(getattr(act, 'departed_at', 0) or 0)
        all_acts.append({
            'provider': 'ridewithgps',
            'id': getattr(act, 'ridewithgps_id', None),
            'timestamp': ts,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })

    # Group by (date, distance) rounded to nearest 0.05 mile for fuzzy matching
    def keyfunc(act):
        # Convert UTC timestamp to home timezone for grouping
        if act['timestamp']:
            utc = datetime.fromtimestamp(int(act['timestamp']), timezone.utc)
            dt = utc.astimezone(home_tz)
        else:
            utc = datetime.fromtimestamp(0, timezone.utc)
            dt = utc.astimezone(home_tz)

        # For date matching, always use midnight
        date_key = dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Round distance to nearest 0.5 mile for more flexible matching
        # This means activities within 0.5 miles of each other will match
        distance_key = round(act['distance'] / 0.5) * 0.5

        # If this is a spreadsheet activity (which only has date precision)
        # or if the time is exactly midnight (suggesting date-only precision)
        is_date_only = (
            act['provider'] == 'spreadsheet' or 
            (dt.hour == 0 and dt.minute == 0 and dt.second == 0)
        )

        return (date_key, distance_key, is_date_only)
    # First, group by date and distance
    initial_groups = defaultdict(list)
    for act in all_acts:
        date_key, distance_key, is_date_only = keyfunc(act)
        initial_groups[(date_key, distance_key)].append(act)
    
    # Then merge groups that are on the same day if any activity in the group is date-only
    grouped = defaultdict(list)
    processed_keys = set()
    
    # Sort keys by date and distance for consistent merging
    sorted_keys = sorted(initial_groups.keys())
    
    for key in sorted_keys:
        if key in processed_keys:
            continue
            
        date_key, distance_key = key
        merged_group = initial_groups[key]
        processed_keys.add(key)
        
        # If any activity in this group is date-only precision
        if any(keyfunc(act)[2] for act in merged_group):
            # Look for other groups on the same day with similar distances
            for other_key in sorted_keys:
                if other_key in processed_keys:
                    continue
                    
                other_date, other_distance = other_key
                if (other_date == date_key and 
                    abs(other_distance - distance_key) <= 0.5):
                    merged_group.extend(initial_groups[other_key])
                    processed_keys.add(other_key)
        
        if merged_group:  # Only add non-empty groups
            grouped[key] = merged_group

    # Build rows for the table
    rows = []
    for group in grouped.values():
        # Find the earliest start time in the group for ordering, converting from UTC to home timezone
        start = min(
            datetime.fromtimestamp(int(a['timestamp']), timezone.utc).astimezone(home_tz) if a['timestamp']
            else datetime.fromtimestamp(0, timezone.utc).astimezone(home_tz)
            for a in group
        )
        ids = {'garmin': None, 'strava': None, 'spreadsheet': None, 'ridewithgps': None}
        names = {'garmin': '', 'strava': '', 'spreadsheet': '', 'ridewithgps': ''}
        dists = {'garmin': None, 'strava': None, 'spreadsheet': None, 'ridewithgps': None}
        for a in group:
            ids[a['provider']] = a['id']
            names[a['provider']] = getattr(a['obj'], 'name', getattr(a['obj'], 'notes', ''))
            dists[a['provider']] = a['distance']
        rows.append({
            'start': start,
            'garmin': ids['garmin'],
            'strava': ids['strava'],
            'spreadsheet': ids['spreadsheet'],
            'ridewithgps': ids['ridewithgps'],
            'garmin_name': names['garmin'],
            'strava_name': names['strava'],
            'spreadsheet_name': names['spreadsheet'],
            'ridewithgps_name': names['ridewithgps'],
            'garmin_dist': dists['garmin'],
            'strava_dist': dists['strava'],
            'spreadsheet_dist': dists['spreadsheet'],
            'ridewithgps_dist': dists['ridewithgps']
        })
    # Sort by start time
    rows.sort(key=lambda r: r['start'])

    # Print table header and rows using tabulate for alignment
    table = []
    for row in rows:
        dist = next((d for d in [row['garmin_dist'], row['strava_dist'], row['spreadsheet_dist'], row['ridewithgps_dist']] if d), '')
        name = next((n for n in [row['garmin_name'], row['strava_name'], row['spreadsheet_name'], row['ridewithgps_name']] if n), '')
        table.append([
            row['start'].strftime('%Y-%m-%d %H:%M'),
            color_id(row['garmin'], row['garmin'] is not None),
            color_id(row['strava'], row['strava'] is not None),
            color_id(row['spreadsheet'], row['spreadsheet'] is not None),
            color_id(row['ridewithgps'], row['ridewithgps'] is not None),
            dist,
            name
        ])
    headers = [
        'Start', 'Garmin ID', 'Strava ID', 'Spreadsheet ID', 'RideWithGPS ID', 'Distance (mi)', 'Name'
    ]
    print(tabulate(table, headers=headers, tablefmt='plain', stralign='left', numalign='right', colalign=("left", "left", "left", "left", "left", "right", "left")))
    print("\nLegend: \033[42mID exists\033[0m, \033[43mTBD = needs to be created\033[0m")
