import os
import json
from pathlib import Path
from fitler.providers.spreadsheet import SpreadsheetActivities
from fitler.providers.strava import StravaActivities
from fitler.providers.ridewithgps import RideWithGPSActivities
# from fitler.providers.garmin import GarminActivities  # Uncomment if implemented
from datetime import datetime, timezone
from dateutil.parser import parse as dateparse
from dateutil.relativedelta import relativedelta
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

def to_utc(dt):
    # If no timezone info, assume local
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt

def run(year_month):
    config = load_config()
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
    try:
        ridewithgps = RideWithGPSActivities()
        ridewithgps_acts = ridewithgps.fetch_activities_for_month(year_month)
    except Exception:
        pass

    # Build a list of all activities by date/distance for matching
    all_acts = []
    for act in spreadsheet_acts:
        dt = dateparse(getattr(act, 'start_time', getattr(act, 'start_date', '')))
        dt = to_utc(dt)
        all_acts.append({
            'provider': 'spreadsheet',
            'id': getattr(act, 'spreadsheet_id', None),
            'start': dt,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })
    for act in strava_acts:
        dt = dateparse(getattr(act, 'start_time', getattr(act, 'start_date', '')))
        dt = to_utc(dt)
        all_acts.append({
            'provider': 'strava',
            'id': getattr(act, 'strava_id', None),
            'start': dt,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })
    for act in garmin_acts:
        dt = dateparse(getattr(act, 'start_time', getattr(act, 'start_date', '')))
        dt = to_utc(dt)
        all_acts.append({
            'provider': 'garmin',
            'id': getattr(act, 'garmin_id', None),
            'start': dt,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })
    for act in ridewithgps_acts:
        dt = dateparse(getattr(act, 'start_time', getattr(act, 'start_date', '')))
        dt = to_utc(dt)
        all_acts.append({
            'provider': 'ridewithgps',
            'id': getattr(act, 'ridewithgps_id', None),
            'start': dt,
            'distance': getattr(act, 'distance', 0),
            'obj': act
        })

    # Group by (date, distance) rounded to nearest 0.05 mile for fuzzy matching
    def keyfunc(act):
        return (
            act['start'].replace(hour=0, minute=0, second=0, microsecond=0),
            round(act['distance'] / 0.05) * 0.05
        )
    grouped = defaultdict(list)
    for act in all_acts:
        grouped[keyfunc(act)].append(act)

    # Build rows for the table
    rows = []
    for group in grouped.values():
        # Find the earliest start time in the group for ordering
        start = min(a['start'] for a in group)
        ids = {'garmin': None, 'strava': None, 'spreadsheet': None, 'ridewithgps': None}
        names = {'garmin': '', 'strava': '', 'spreadsheet': '', 'ridewithgps': ''}
        dists = {'garmin': None, 'strava': None, 'spreadsheet': None, 'ridewithgps': None}
        for a in group:
            ids[a['provider']] = a['id']
            names[a['provider']] = getattr(a['obj'], 'name', getattr(a['obj'], 'title', ''))
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
