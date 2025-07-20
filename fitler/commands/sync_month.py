import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from fitler.providers.spreadsheet import SpreadsheetActivities
from fitler.providers.strava import StravaActivities
from fitler.providers.ridewithgps import RideWithGPSActivities
from fitler.metadata import ActivityMetadata, db
from datetime import datetime, timezone
from collections import defaultdict
from tabulate import tabulate

CONFIG_PATH = Path("fitler_config.json")

# ANSI color codes for terminal output
green_bg = '\033[42m'
yellow_bg = '\033[43m'
red_bg = '\033[41m'
reset = '\033[0m'

def load_config():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    if "debug" not in config:
        config["debug"] = False
    if "provider_priority" not in config:
        config["provider_priority"] = "spreadsheet,ridewithgps,strava"
    return config

def color_id(id_val, exists):
    if exists:
        return f"{green_bg}{id_val}{reset}"
    else:
        return f"{yellow_bg}TBD{reset}"



def color_text(text, is_auth, is_new, is_wrong):
    """Apply color highlighting to text based on its status."""
    if is_auth:  # Authoritative source
        return f"{green_bg}{text}{reset}"
    elif is_new:  # New activity to be created
        return f"{yellow_bg}{text}{reset}"
    elif is_wrong:  # Different from authoritative source
        return f"{red_bg}{text}{reset}"
    return text  # No highlighting needed

def highlight_provider_id(sheet_id, actual_id, provider):
    """Highlight provider IDs based on their status in the spreadsheet."""
    if not sheet_id and actual_id:
        # Missing in spreadsheet but exists in provider
        return f"{yellow_bg}{actual_id}{reset}"
    elif sheet_id and actual_id and str(sheet_id) != str(actual_id):
        # Present in spreadsheet but doesn't match
        return f"{red_bg}{sheet_id}{reset}"
    elif sheet_id:
        # Present and correct
        return str(sheet_id)
    return ""  # No ID available

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

    # Ensure database connection is open
    db.connect()
    
    # First, find or create ActivityMetadata records for each provider's activities
    all_acts = []
    
    def process_activity(act, provider: str):
        # Get the timestamp and ID
        ts = int(getattr(act, 'departed_at', 0) or 0)
        provider_id = getattr(act, f'{provider}_id', None)
        
        # Try to find existing record by provider ID
        metadata = None
        lookup_id = provider_id
        if provider == 'spreadsheet':
            lookup_id = getattr(act, 'spreadsheet_id', None)
        
        if lookup_id:
            try:
                metadata = ActivityMetadata.select().where(getattr(ActivityMetadata, f'{provider}_id') == lookup_id).first()
            except Exception:
                pass
        
        # If not found by ID, create new record
        if not metadata:
            metadata = ActivityMetadata()
            # Set basic fields
            if ts:
                dt = datetime.fromtimestamp(ts, timezone.utc)
                eastern = dt.astimezone(home_tz)
                metadata.start_time = eastern
                metadata.date = eastern.date()
            metadata.save()  # Save to create the record and get an ID
            
        # Convert activity data to dict for storage
        act_data = {
            'id': provider_id if provider != 'spreadsheet' else getattr(act, 'spreadsheet_id', None),
            'name': getattr(act, 'name', getattr(act, 'notes', '')),
            'notes': getattr(act, 'notes', ''),
            'equipment': getattr(act, 'equipment', ''),
            'distance': getattr(act, 'distance', 0),
            'activity_type': getattr(act, 'activity_type', ''),
            'start_time': datetime.fromtimestamp(ts, timezone.utc) if ts else None
        }
        
        # Set the provider ID directly first
        if provider_id:
            setattr(metadata, f'{provider}_id', provider_id)
            metadata.save()
        
        # Then update the rest of the metadata
        metadata.update_from_provider(provider, act_data, config)
        
        return {
            'provider': provider,
            'id': provider_id,
            'timestamp': ts,
            'distance': getattr(act, 'distance', 0),
            'obj': act,
            'metadata': metadata
        }
    
    # Process activities from each provider
    for act in spreadsheet_acts:
        all_acts.append(process_activity(act, 'spreadsheet'))
    for act in strava_acts:
        all_acts.append(process_activity(act, 'strava'))
    for act in ridewithgps_acts:
        all_acts.append(process_activity(act, 'ridewithgps'))

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
        ids = {'strava': None, 'spreadsheet': None, 'ridewithgps': None}
        names = {'strava': '', 'spreadsheet': '', 'ridewithgps': ''}
        dists = {'strava': None, 'spreadsheet': None, 'ridewithgps': None}
        for a in group:
            ids[a['provider']] = a['id']
            names[a['provider']] = getattr(a['obj'], 'name', getattr(a['obj'], 'notes', ''))
            dists[a['provider']] = a['distance']
        spreadsheet_obj = next((a['obj'] for a in group if a['provider'] == 'spreadsheet'), None)
        # Get provider IDs from spreadsheet if they exist
        sheet_strava_id = getattr(spreadsheet_obj, 'strava_id', '') if spreadsheet_obj else ''
        sheet_garmin_id = getattr(spreadsheet_obj, 'garmin_id', '') if spreadsheet_obj else ''
        sheet_ridewithgps_id = getattr(spreadsheet_obj, 'ridewithgps_id', '') if spreadsheet_obj else ''
        
        rows.append({
            'start': start,
            'strava': ids['strava'],
            'spreadsheet': ids['spreadsheet'],
            'ridewithgps': ids['ridewithgps'],
            'strava_name': names['strava'],
            'spreadsheet_name': names['spreadsheet'],
            'ridewithgps_name': names['ridewithgps'],
            'strava_dist': dists['strava'],
            'spreadsheet_dist': dists['spreadsheet'],
            'ridewithgps_dist': dists['ridewithgps'],
            'strava_obj': next((a['obj'] for a in group if a['provider'] == 'strava'), None),
            'spreadsheet_obj': spreadsheet_obj,
            'ridewithgps_obj': next((a['obj'] for a in group if a['provider'] == 'ridewithgps'), None),
            'sheet_strava_id': sheet_strava_id,
            'sheet_garmin_id': sheet_garmin_id,
            'sheet_ridewithgps_id': sheet_ridewithgps_id
        })
    # Sort by start time
    rows.sort(key=lambda r: r['start'])

    # Print table header and rows using tabulate for alignment
    table = []
    all_changes = []  # Collect all needed changes
    
    for row in rows:
        # Get the metadata object for this group by matching IDs
        metadata = None
        for act in all_acts:
            if (act['provider'] == 'strava' and act['id'] == row['strava']) or \
               (act['provider'] == 'spreadsheet' and act['id'] == row['spreadsheet']) or \
               (act['provider'] == 'ridewithgps' and act['id'] == row['ridewithgps']):
                metadata = act['metadata']
                break
        
        if not metadata:
            # If we couldn't find by ID, try matching by timestamp as fallback
            metadata = next((act['metadata'] for act in all_acts 
                           if act['timestamp'] == int(row['start'].timestamp())), None)
        
        if not metadata:
            # If we still can't find it, create a new one
            metadata = ActivityMetadata()
            metadata.start_time = row['start']
        
        # Get the authoritative provider and data
        auth_provider = metadata.get_authoritative_provider(
            config.get("provider_priority", "spreadsheet,ridewithgps,strava").split(",")
        )
        
        # Get authoritative name and equipment if they exist
        auth_data = metadata.get_provider_data(auth_provider) if auth_provider else None
        auth_name = auth_data.get('name') if auth_data else None
        auth_equipment = auth_data.get('equipment') if auth_data else None
        
        # Collect changes needed for this activity
        changes = metadata.get_needed_changes(config)
        if changes:
            all_changes.extend(changes)

        dist = next((d for d in [row['strava_dist'], row['spreadsheet_dist'], row['ridewithgps_dist']] if d), '')
        
        # Helper function to determine text highlighting
        def highlight(provider, text, is_name=True):
            """Highlight text based on provider authority and data matching."""
            if not metadata or (not text and provider != 'spreadsheet'):
                return ''
            
            provider_order = config.get("provider_priority", "spreadsheet,ridewithgps,strava").split(",")
            auth_provider = metadata.get_authoritative_provider(provider_order) if metadata else None
            
            # Get provider and authoritative data
            provider_data = metadata.get_provider_data(provider) if metadata else None
            auth_data = metadata.get_provider_data(auth_provider) if auth_provider and metadata else None
            
            # If this is the spreadsheet and it's missing
            if provider == 'spreadsheet' and not getattr(metadata, 'spreadsheet_data', None):
                # Show what will be created from the authoritative source
                if auth_data:
                    field = 'name' if is_name else 'equipment'
                    return color_text(auth_data.get(field, ''), False, True, False)
                return ''
            
            # Get the authoritative value for comparison
            auth_value = None
            if auth_data:
                field = 'name' if is_name else 'equipment'
                auth_value = auth_data.get(field)
            
            # If this is the authoritative provider
            if provider == auth_provider:
                return color_text(text, True, False, False)
            
            # If this provider matches the authoritative data
            if auth_value and text == auth_value:
                return color_text(text, True, False, False)
            
            # If this provider has data but doesn't match
            if auth_value and text != auth_value:
                return color_text(text, False, False, True)
            
            # If no authoritative source exists yet
            if not auth_provider:
                return color_text(text, False, True, False)
            
            return text

        table.append([
            row['start'].strftime('%Y-%m-%d %H:%M'),
            color_id(row['strava'], row['strava'] is not None),
            highlight('strava', row['strava_name'] or ''),
            highlight('strava', getattr(row['strava_obj'], 'equipment', '') if row.get('strava_obj') else '', False),
            color_id(row['spreadsheet'], row['spreadsheet'] is not None),
            highlight('spreadsheet', row['spreadsheet_name'] or ''),
            highlight('spreadsheet', getattr(row['spreadsheet_obj'], 'equipment', '') if row.get('spreadsheet_obj') else '', False),
            color_id(row['ridewithgps'], row['ridewithgps'] is not None),
            highlight('ridewithgps', row['ridewithgps_name'] or ''),
            highlight('ridewithgps', getattr(row['ridewithgps_obj'], 'equipment', '') if row.get('ridewithgps_obj') else '', False),
            dist,
            # Add provider IDs from spreadsheet with highlighting
            highlight_provider_id(row['sheet_strava_id'], row['strava'], 'strava'),
            highlight_provider_id(row['sheet_garmin_id'], None, 'garmin'),  # Garmin data not available yet
            highlight_provider_id(row['sheet_ridewithgps_id'], row['ridewithgps'], 'ridewithgps')
        ])

    headers = [
        'Start',
        'Strava ID', 'Strava Name', 'Strava Equip',
        'Sheet ID', 'Sheet Name', 'Sheet Equip',
        'RWGPS ID', 'RWGPS Name', 'RWGPS Equip',
        'Distance (mi)',
        'Sheet: Strava ID', 'Sheet: Garmin ID', 'Sheet: RWGPS ID'
    ]
    print(tabulate(table, headers=headers, tablefmt='plain', stralign='left', numalign='left', colalign=("left",) * len(headers)))
    print("\nLegend:")
    print(f"{green_bg}Green{reset} = Source of truth (from highest priority provider)")
    print(f"{yellow_bg}Yellow{reset} = New entry to be created")
    print(f"{red_bg}Red{reset} = Needs to be updated to match source of truth")
    
    if all_changes:
        print("\nChanges needed:")
        for change in all_changes:
            print(f"* {change}")
            
    # Close database connection
    db.close()
