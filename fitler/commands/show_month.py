import logging
import datetime
from fitler.core import Fitler

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
    """Show activities for a specific year and month (format: YYYY-MM)."""
    if not year_month:
        print("Please provide a year and month in YYYY-MM format")
        return

    # Initialize Fitler
    with Fitler() as fitler:
        # Get all activities for the month
        activities = fitler.fetch_activities_for_month(year_month)
        
        # Use fitler's config and timezone
        home_tz = fitler.home_tz

        # Print activities from each source
        print_activities("Spreadsheet", activities['spreadsheet'], "spreadsheet_id", home_tz)
        print_activities("Strava", activities['strava'], "strava_id", home_tz)
        print_activities("RideWithGPS", activities['ridewithgps'], "ridewithgps_id", home_tz)
