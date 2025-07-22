import datetime
from fitler.core import Fitler


def print_activities(provider_name, activities, id_field, home_tz):
    print(f"\n{provider_name} (for selected month):")
    print(
        f"{'ID':<12} {'Name':<30} {'Raw Timestamp':<12} {'Local Time':<19} {'Distance (mi)':>12}"
    )
    print("-" * 85)
    for act in activities:
        act_id = getattr(act, id_field, None)
        name = getattr(act, "name", None) or getattr(act, "notes", "")

        # start_time is stored as a Unix timestamp (integer/string)
        start_time = getattr(act, "start_time", None)
        date_str = ""
        raw_timestamp = "None"

        if start_time:
            try:
                # Convert Unix timestamp to datetime
                if isinstance(start_time, str):
                    timestamp = int(start_time)
                else:
                    timestamp = int(start_time)

                # Create UTC datetime from timestamp
                utc_dt = datetime.datetime.fromtimestamp(
                    timestamp, datetime.timezone.utc
                )
                # Convert to local timezone
                local_dt = utc_dt.astimezone(home_tz)

                raw_timestamp = str(timestamp)
                date_str = f"{local_dt.strftime('%Y-%m-%d %H:%M')} {local_dt.tzname()}"
            except (ValueError, TypeError):
                date_str = "invalid"
                raw_timestamp = str(start_time) if start_time else "None"

        dist = getattr(act, "distance", 0)
        line = (
            f"{str(act_id):<12} {str(name)[:28]:<30} "
            f"{str(raw_timestamp):<12} {str(date_str):<19} {dist:12.2f}"
        )
        print(line)


def run(year_month):
    """Show activities for a specific year and month (format: YYYY-MM)."""
    if not year_month:
        print("Please provide a year and month in YYYY-MM format")
        return

    with Fitler() as fitler:
        activities = fitler.pull_activities(year_month)

        home_tz = fitler.home_tz

        provider_configs = {
            "spreadsheet": ("Spreadsheet", "spreadsheet_id"),
            "strava": ("Strava", "strava_id"),
            "ridewithgps": ("RideWithGPS", "ridewithgps_id"),
            "garmin": ("Garmin", "garmin_id"),
        }

        for provider_key, (display_name, id_field) in provider_configs.items():
            if provider_key in activities:
                print_activities(
                    display_name, activities[provider_key], id_field, home_tz
                )
