from typing import Optional, NamedTuple
from enum import Enum
from fitler.activity import Activity
from fitler.core import Fitler
from datetime import datetime, timezone
import dateparser
from collections import defaultdict
from tabulate import tabulate


class ChangeType(Enum):
    UPDATE_NAME = "Update Name"
    UPDATE_EQUIPMENT = "Update Equipment"
    ADD_ACTIVITY = "Add Activity"
    LINK_ACTIVITY = "Link Activity"


class ActivityChange(NamedTuple):
    change_type: ChangeType
    provider: str
    activity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    source_provider: Optional[str] = None

    def __str__(self) -> str:
        if self.change_type == ChangeType.UPDATE_NAME:
            return (
                f"Update {self.provider} name for activity {self.activity_id} "
                f"from '{self.old_value}' to '{self.new_value}'"
            )
        elif self.change_type == ChangeType.UPDATE_EQUIPMENT:
            return (
                f"Update {self.provider} equipment for activity {self.activity_id} "
                f"from '{self.old_value}' to '{self.new_value}'"
            )
        elif self.change_type == ChangeType.ADD_ACTIVITY:
            return (
                f"Add activity '{self.new_value}' to {self.provider} "
                f"(from {self.source_provider} activity {self.activity_id})"
            )
        elif self.change_type == ChangeType.LINK_ACTIVITY:
            return (
                f"Link {self.provider} activity {self.activity_id} "
                f"with {self.source_provider} activity {self.new_value}"
            )
        return "Unknown change"


# ANSI color codes for terminal output
green_bg = "\033[42m"
yellow_bg = "\033[43m"
red_bg = "\033[41m"
reset = "\033[0m"


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


def process_activity_for_display(activity: Activity, provider: str) -> dict:
    """Process an Activity object for display/matching purposes."""
    # Get the provider-specific ID
    provider_id = getattr(activity, f"{provider}_id", None)

    # Convert start time to timestamp
    if activity.start_time:
        try:
            # If it's already a timestamp string, use it
            if isinstance(activity.start_time, str):
                ts = int(activity.start_time)
            # If it's a datetime object, convert directly
            elif isinstance(activity.start_time, datetime):
                ts = int(activity.start_time.timestamp())
            else:
                # Handle other formats
                start_dt = dateparser.parse(str(activity.start_time))
                ts = int(start_dt.timestamp()) if start_dt else 0
        except (AttributeError, TypeError, ValueError):
            ts = 0
    else:
        ts = 0

    return {
        "provider": provider,
        "id": provider_id,
        "timestamp": ts,
        "distance": activity.distance or 0,
        "obj": activity,  # Use the actual Activity object
        "metadata": activity,
    }


def run(year_month):
    with Fitler() as fitler:
        # Use the new pull_activities method
        activities = fitler.pull_activities(year_month)

        spreadsheet_acts = activities.get("spreadsheet", [])
        strava_acts = activities.get("strava", [])
        ridewithgps_acts = activities.get("ridewithgps", [])
        garmin_acts = activities.get("garmin", [])

        config = fitler.config
        home_tz = fitler.home_tz

    all_acts = []

    # Process activities from each provider - these are now Activity objects
    for act in spreadsheet_acts:
        all_acts.append(process_activity_for_display(act, "spreadsheet"))
    for act in strava_acts:
        all_acts.append(process_activity_for_display(act, "strava"))
    for act in ridewithgps_acts:
        all_acts.append(process_activity_for_display(act, "ridewithgps"))
    for act in garmin_acts:
        all_acts.append(process_activity_for_display(act, "garmin"))

    # Group by (date, distance) rounded to nearest 0.05 mile for fuzzy matching
    def keyfunc(act):
        # Convert UTC timestamp to home timezone for grouping
        if act["timestamp"]:
            utc = datetime.fromtimestamp(int(act["timestamp"]), timezone.utc)
            dt = utc.astimezone(home_tz)
        else:
            utc = datetime.fromtimestamp(0, timezone.utc)
            dt = utc.astimezone(home_tz)

        # For date matching, always use midnight
        date_key = dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Round distance to nearest 0.5 mile for more flexible matching
        # This means activities within 0.5 miles of each other will match
        distance_key = round(act["distance"] / 0.5) * 0.5

        # If this is a spreadsheet activity (which only has date precision)
        # or if the time is exactly midnight (suggesting date-only precision)
        is_date_only = act["provider"] == "spreadsheet" or (
            dt.hour == 0 and dt.minute == 0 and dt.second == 0
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
                if other_date == date_key and abs(other_distance - distance_key) <= 0.5:
                    merged_group.extend(initial_groups[other_key])
                    processed_keys.add(other_key)

        if merged_group:  # Only add non-empty groups
            grouped[key] = merged_group

    # Build rows for the table
    rows = []
    for group in grouped.values():
        # Find the earliest start time in the group for ordering,
        # converting from UTC to home timezone
        start = min(
            (
                datetime.fromtimestamp(int(a["timestamp"]), timezone.utc).astimezone(
                    home_tz
                )
                if a["timestamp"]
                else datetime.fromtimestamp(0, timezone.utc).astimezone(home_tz)
            )
            for a in group
        )
        ids = {"strava": None, "spreadsheet": None, "ridewithgps": None, "garmin": None}
        names = {"strava": "", "spreadsheet": "", "ridewithgps": "", "garmin": ""}
        dists = {
            "strava": None,
            "spreadsheet": None,
            "ridewithgps": None,
            "garmin": None,
        }
        for a in group:
            ids[a["provider"]] = a["id"]
            names[a["provider"]] = getattr(
                a["obj"], "name", getattr(a["obj"], "notes", "")
            )
            dists[a["provider"]] = a["distance"]
        spreadsheet_obj = next(
            (a["obj"] for a in group if a["provider"] == "spreadsheet"), None
        )
        # Get provider IDs from spreadsheet if they exist
        sheet_strava_id = (
            getattr(spreadsheet_obj, "strava_id", "") if spreadsheet_obj else ""
        )
        sheet_garmin_id = (
            getattr(spreadsheet_obj, "garmin_id", "") if spreadsheet_obj else ""
        )
        sheet_ridewithgps_id = (
            getattr(spreadsheet_obj, "ridewithgps_id", "") if spreadsheet_obj else ""
        )

        rows.append(
            {
                "start": start,
                "strava": ids["strava"],
                "spreadsheet": ids["spreadsheet"],
                "ridewithgps": ids["ridewithgps"],
                "garmin": ids["garmin"],
                "strava_name": names["strava"],
                "spreadsheet_name": names["spreadsheet"],
                "ridewithgps_name": names["ridewithgps"],
                "garmin_name": names["garmin"],
                "strava_dist": dists["strava"],
                "spreadsheet_dist": dists["spreadsheet"],
                "ridewithgps_dist": dists["ridewithgps"],
                "garmin_dist": dists["garmin"],
                "strava_obj": next(
                    (a["obj"] for a in group if a["provider"] == "strava"), None
                ),
                "spreadsheet_obj": spreadsheet_obj,
                "ridewithgps_obj": next(
                    (a["obj"] for a in group if a["provider"] == "ridewithgps"), None
                ),
                "garmin_obj": next(
                    (a["obj"] for a in group if a["provider"] == "garmin"), None
                ),
                "sheet_strava_id": sheet_strava_id,
                "sheet_garmin_id": sheet_garmin_id,
                "sheet_ridewithgps_id": sheet_ridewithgps_id,
            }
        )
    # Sort by start time
    rows.sort(key=lambda r: r["start"])

    # Print table header and rows using tabulate for alignment
    table = []
    all_changes = []  # Collect all needed changes

    if not rows:
        print(f"\nNo activities found for {year_month}")
        return

    for row in rows:
        # Get the metadata object for this group by matching IDs
        metadata = None
        for act in all_acts:
            if (
                (act["provider"] == "strava" and act["id"] == row["strava"])
                or (
                    act["provider"] == "spreadsheet" and act["id"] == row["spreadsheet"]
                )
                or (
                    act["provider"] == "ridewithgps" and act["id"] == row["ridewithgps"]
                )
                or (act["provider"] == "garmin" and act["id"] == row["garmin"])
            ):
                metadata = act["metadata"]
                break

        if not metadata:
            # If we couldn't find by ID, try matching by timestamp as fallback
            metadata = next(
                (
                    act["metadata"]
                    for act in all_acts
                    if act["timestamp"] == int(row["start"].timestamp())
                ),
                None,
            )

        if not metadata:
            # If we still can't find it, create a new one
            metadata = Activity()
            metadata.start_time = row["start"]

        # Get the authoritative provider and data
        auth_provider = metadata.get_authoritative_provider(
            config.get("provider_priority", "spreadsheet,ridewithgps,strava").split(",")
        )

        # Get authoritative name and equipment if they exist
        auth_data = metadata.get_provider_data(auth_provider) if auth_provider else None
        auth_name = auth_data.get("name") if auth_data else None
        auth_equipment = auth_data.get("equipment") if auth_data else None

        # Collect changes needed for this activity
        activity_changes = []

        # Get authoritative provider's data
        provider_priority = config.get(
            "provider_priority", "spreadsheet,ridewithgps,strava"
        ).split(",")
        auth_provider = metadata.get_authoritative_provider(provider_priority)
        auth_data = metadata.get_provider_data(auth_provider) if auth_provider else None

        # Check each provider for needed changes
        for provider in ["strava", "ridewithgps", "spreadsheet", "garmin"]:
            # Only proceed with change detection if we have an authoritative
            # source and this isn't it
            if not auth_provider or provider == auth_provider:
                continue

            # Get the activity objects from the row for this provider
            activity_obj = row.get(f"{provider}_obj")

            # For spreadsheet provider ID checks
            if provider == "spreadsheet":
                # Check if spreadsheet's stored provider IDs match actual IDs
                actual_strava_id = row.get("strava")
                actual_rwgps_id = row.get("ridewithgps")
                sheet_strava_id = row.get("sheet_strava_id")
                sheet_rwgps_id = row.get("sheet_ridewithgps_id")

                if actual_strava_id and str(actual_strava_id) != str(
                    sheet_strava_id or ""
                ):
                    activity_changes.append(
                        ActivityChange(
                            change_type=ChangeType.LINK_ACTIVITY,
                            provider="spreadsheet",
                            activity_id=str(row["spreadsheet"]),
                            new_value=str(actual_strava_id),
                            source_provider="strava",
                        )
                    )

                # Check for RWGPS ID mismatches
                # The spreadsheet might have a wrong ID or an ID when there shouldn't be one
                if str(actual_rwgps_id or "") != str(sheet_rwgps_id or ""):
                    activity_changes.append(
                        ActivityChange(
                            change_type=ChangeType.LINK_ACTIVITY,
                            provider="spreadsheet",
                            activity_id=str(row["spreadsheet"]),
                            new_value=str(actual_rwgps_id or ""),
                            source_provider="ridewithgps",
                        )
                    )

            # Get the data for comparison
            auth_equipment = auth_data.get("equipment", "") if auth_data else ""
            provider_equipment = (
                getattr(activity_obj, "equipment", "") if activity_obj else ""
            )
            auth_name = auth_data.get("name", "") if auth_data else ""
            provider_name = getattr(activity_obj, "name", "") if activity_obj else ""

            # Check if equipment needs updating
            if (
                auth_equipment
                and provider_equipment
                and auth_equipment != provider_equipment
            ):
                activity_changes.append(
                    ActivityChange(
                        change_type=ChangeType.UPDATE_EQUIPMENT,
                        provider=provider,
                        activity_id=str(row[provider]),
                        old_value=provider_equipment,
                        new_value=auth_equipment,
                    )
                )

            # Check if name needs updating
            if auth_name and provider_name and auth_name != provider_name:
                activity_changes.append(
                    ActivityChange(
                        change_type=ChangeType.UPDATE_NAME,
                        provider=provider,
                        activity_id=str(row[provider]),
                        old_value=provider_name,
                        new_value=auth_name,
                    )
                )

        if activity_changes:
            all_changes.extend(activity_changes)

        dist = next(
            (
                d
                for d in [
                    row["strava_dist"],
                    row["spreadsheet_dist"],
                    row["ridewithgps_dist"],
                ]
                if d
            ),
            "",
        )

        # Helper function to determine text highlighting
        def highlight(provider, text, is_name=True):
            """Highlight text based on provider authority and data matching."""
            if not metadata or (not text and provider != "spreadsheet"):
                return ""

            provider_order = config.get(
                "provider_priority", "spreadsheet,ridewithgps,strava"
            ).split(",")
            auth_provider = (
                metadata.get_authoritative_provider(provider_order)
                if metadata
                else None
            )

            # Get provider and authoritative data
            auth_data = (
                metadata.get_provider_data(auth_provider)
                if auth_provider and metadata
                else None
            )

            # If this is the spreadsheet and it's missing
            if provider == "spreadsheet" and not getattr(
                metadata, "spreadsheet_data", None
            ):
                # Show what will be created from the authoritative source
                if auth_data:
                    field = "name" if is_name else "equipment"
                    return color_text(auth_data.get(field, ""), False, True, False)
                return ""

            # Get the authoritative value for comparison
            auth_value = None
            if auth_data:
                field = "name" if is_name else "equipment"
                auth_value = auth_data.get(field)

            # Only highlight green if this is the actual authoritative provider
            if provider == auth_provider:
                return color_text(text, True, False, False)

            # If this provider has data but doesn't match the authoritative source
            if auth_value and text != auth_value:
                return color_text(text, False, False, True)

            # If no authoritative source exists yet
            if not auth_provider:
                return color_text(text, False, True, False)

            # For all other cases (matches authoritative but isn't authoritative), no highlighting
            return text

        table.append(
            [
                row["start"].strftime("%Y-%m-%d %H:%M"),
                color_id(row["strava"], row["strava"] is not None),
                highlight("strava", row["strava_name"] or ""),
                highlight(
                    "strava",
                    (
                        getattr(row["strava_obj"], "equipment", "")
                        if row.get("strava_obj")
                        else ""
                    ),
                    False,
                ),
                color_id(row["spreadsheet"], row["spreadsheet"] is not None),
                highlight("spreadsheet", row["spreadsheet_name"] or ""),
                highlight(
                    "spreadsheet",
                    (
                        getattr(row["spreadsheet_obj"], "equipment", "")
                        if row.get("spreadsheet_obj")
                        else ""
                    ),
                    False,
                ),
                color_id(row["ridewithgps"], row["ridewithgps"] is not None),
                highlight("ridewithgps", row["ridewithgps_name"] or ""),
                highlight(
                    "ridewithgps",
                    (
                        getattr(row["ridewithgps_obj"], "equipment", "")
                        if row.get("ridewithgps_obj")
                        else ""
                    ),
                    False,
                ),
                color_id(row["garmin"], row["garmin"] is not None),
                highlight("garmin", row["garmin_name"] or ""),
                highlight(
                    "garmin",
                    (
                        getattr(row["garmin_obj"], "equipment", "")
                        if row.get("garmin_obj")
                        else ""
                    ),
                    False,
                ),
                dist,
                # Add provider IDs from spreadsheet with highlighting
                highlight_provider_id(row["sheet_strava_id"], row["strava"], "strava"),
                highlight_provider_id(row["sheet_garmin_id"], row["garmin"], "garmin"),
                highlight_provider_id(
                    row["sheet_ridewithgps_id"], row["ridewithgps"], "ridewithgps"
                ),
            ]
        )

    headers = [
        "Start",
        "Strava ID",
        "Strava Name",
        "Strava Equip",
        "Sheet ID",
        "Sheet Name",
        "Sheet Equip",
        "RWGPS ID",
        "RWGPS Name",
        "RWGPS Equip",
        "Garmin ID",
        "Garmin Name",
        "Garmin Equip",
        "Distance (mi)",
        "Sheet: Strava ID",
        "Sheet: Garmin ID",
        "Sheet: RWGPS ID",
    ]
    print(
        tabulate(
            table,
            headers=headers,
            tablefmt="plain",
            stralign="left",
            numalign="left",
            colalign=("left",) * len(headers),
        )
    )
    print("\nLegend:")
    print(f"{green_bg}Green{reset} = Source of truth (from highest priority provider)")
    print(f"{yellow_bg}Yellow{reset} = New entry to be created")
    print(f"{red_bg}Red{reset} = Needs to be updated to match source of truth")

    if all_changes:
        # Group changes by type for better readability
        changes_by_type = defaultdict(list)
        for change in all_changes:
            changes_by_type[change.change_type].append(change)

        print("\nChanges needed:")
        for change_type in ChangeType:
            if changes_by_type[change_type]:
                print(f"\n{change_type.value}s:")
                for change in changes_by_type[change_type]:
                    print(f"* {change}")
