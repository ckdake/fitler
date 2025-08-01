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

def get_months():
    now = datetime.datetime.now()
    earliest = datetime.datetime(2000, 1, 1)
    months = []
    current = now.replace(day=1)
    while current >= earliest:
        months.append(current.strftime("%Y-%m"))
        if current.month == 1:
            current = current.replace(year=current.year - 1, month=12)
        else:
            current = current.replace(month=current.month - 1)
    return months
        
def run(year_month):
    """Show activities for a specific year and month (format: YYYY-MM)."""
    if not year_month:
        print("Please provide a year and month in YYYY-MM format")
        return

    with Fitler() as fitler:
        enabled_providers = fitler.enabled_providers
        if not enabled_providers:
            print("No providers are enabled. Check your configuration.")
            return
    
        activities = fitler.pull_activities(year_month)

        home_tz = fitler.home_tz

        months = [year_month] if year_month else get_months()
        for month in months:
            print(f"\n=== {month} ===")
            activities = fitler.pull_activities(year_month)

            for provider_name, provider_activities in activities.items():
                if provider_activities:  # Only show providers that have activities
                    display_name = provider_name.title()  # Capitalize first letter
                    print_activities(
                        display_name, provider_activities, "provider_id", home_tz
                    )
