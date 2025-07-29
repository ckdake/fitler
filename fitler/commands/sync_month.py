from typing import Optional, NamedTuple, Dict, List, Any
from enum import Enum
from fitler.core import Fitler
from datetime import datetime, timezone
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


def process_activity_for_display(activity, provider: str) -> dict:
    """Process a provider-specific activity object for display/matching purposes."""
    # Get the provider ID using the provider_id property
    provider_id = getattr(activity, "provider_id", None)

    # Get start_time (now stored as integer timestamp)
    start_time = getattr(activity, "start_time", None)
    timestamp = start_time if start_time else 0

    # Get distance
    distance = getattr(activity, "distance", 0)
    if distance is None:
        distance = 0

    return {
        "provider": provider,
        "id": provider_id,
        "timestamp": int(timestamp),
        "distance": float(distance),
        "obj": activity,
        "name": getattr(activity, "name", "") or "",
        "equipment": getattr(activity, "equipment", "") or "",
    }


def generate_correlation_key(timestamp: int, distance: float) -> str:
    """Generate a correlation key for matching activities across providers."""
    if not timestamp or not distance:
        return ""

    try:
        # Convert timestamp to date string
        dt = datetime.fromtimestamp(timestamp, timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")

        # Round distance to nearest 0.1 mile for fuzzy matching
        rounded_distance = round(float(distance) * 10) / 10

        return f"{date_str}_{rounded_distance}"
    except (ValueError, TypeError):
        return ""


def run(year_month):
    with Fitler() as fitler:
        # Use the new pull_activities method to get provider-specific activities
        activities = fitler.pull_activities(year_month)

        config = fitler.config
        home_tz = fitler.home_tz

    # Process all activities from all providers
    all_acts = []

    # Dynamically process activities from all enabled providers
    for provider_name, provider_activities in activities.items():
        for act in provider_activities:
            all_acts.append(process_activity_for_display(act, provider_name))

    if not all_acts:
        print(f"\nNo activities found for {year_month}")
        return

    # Group activities by correlation key (date + distance)
    grouped = defaultdict(list)
    for act in all_acts:
        correlation_key = generate_correlation_key(act["timestamp"], act["distance"])
        if correlation_key:  # Only group activities with valid correlation keys
            grouped[correlation_key].append(act)

    # Build rows for the table
    rows = []
    for group in grouped.values():
        # Skip single-activity groups if they're just one provider
        # (no correlation to show)
        if len(group) == 1:
            continue

        # Find the earliest start time in the group for ordering
        start = min(
            (
                datetime.fromtimestamp(a["timestamp"], timezone.utc).astimezone(home_tz)
                if a["timestamp"]
                else datetime.fromtimestamp(0, timezone.utc).astimezone(home_tz)
            )
            for a in group
        )

        # Organize by provider
        by_provider = {}
        for a in group:
            by_provider[a["provider"]] = a

        rows.append(
            {
                "start": start,
                "providers": by_provider,
                "correlation_key": generate_correlation_key(
                    group[0]["timestamp"], group[0]["distance"]
                ),
            }
        )

    # Sort by start time
    rows.sort(key=lambda r: r["start"])

    # Determine which providers we actually have data for
    all_providers = set()
    for row in rows:
        all_providers.update(row["providers"].keys())

    # Get all enabled providers from config to ensure we show them all
    enabled_providers = []
    provider_config = config.get("providers", {})
    for provider_name, provider_settings in provider_config.items():
        if provider_settings.get("enabled", False):
            enabled_providers.append(provider_name)
    
    # Combine providers that have data with all enabled providers
    all_providers.update(enabled_providers)
    provider_list = sorted(all_providers)

    if not rows:
        print(f"\nNo correlated activities found for {year_month}")
        print("(Activities that exist in only one provider are not shown)")
        return

    # Build table
    table = []
    all_changes = []

    # Determine authoritative provider based on config priority
    # New config structure has priorities as numbers (lower = higher priority)
    provider_priorities = {}
    provider_config = config.get("providers", {})
    
    for provider_name, provider_settings in provider_config.items():
        if provider_settings.get("enabled", False):
            # Default priority is 999 for providers without explicit priority
            priority = provider_settings.get("priority", 999)
            provider_priorities[provider_name] = priority
    
    # Sort providers by priority (lower number = higher priority)
    priority_order = sorted(provider_priorities.items(), key=lambda x: x[1])
    provider_priority = [provider for provider, _ in priority_order]

    for row in rows:
        providers = row["providers"]

        # Find authoritative provider for this group
        auth_provider = None
        for p in provider_priority:
            if p in providers:
                auth_provider = p
                break

        if not auth_provider:
            continue

        auth_activity = providers[auth_provider]
        auth_name = auth_activity["name"]
        auth_equipment = auth_activity["equipment"]

        # Build table row
        table_row = [row["start"].strftime("%Y-%m-%d %H:%M")]

        for provider in provider_list:
            if provider in providers:
                activity = providers[provider]
                # Color code based on authority
                id_colored = color_id(activity["id"], True)

                if provider == auth_provider:
                    name_colored = color_text(activity["name"], True, False, False)
                    equip_colored = color_text(
                        activity["equipment"], True, False, False
                    )
                else:
                    # Check if different from authoritative
                    name_wrong = activity["name"] != auth_name if auth_name else False
                    equip_wrong = (
                        activity["equipment"] != auth_equipment
                        if auth_equipment
                        else False
                    )

                    name_colored = color_text(
                        activity["name"], False, False, name_wrong
                    )
                    equip_colored = color_text(
                        activity["equipment"], False, False, equip_wrong
                    )

                    # Record needed changes
                    if name_wrong and auth_name:
                        all_changes.append(
                            ActivityChange(
                                change_type=ChangeType.UPDATE_NAME,
                                provider=provider,
                                activity_id=str(activity["id"]),
                                old_value=activity["name"],
                                new_value=auth_name,
                            )
                        )

                    if equip_wrong and auth_equipment:
                        all_changes.append(
                            ActivityChange(
                                change_type=ChangeType.UPDATE_EQUIPMENT,
                                provider=provider,
                                activity_id=str(activity["id"]),
                                old_value=activity["equipment"],
                                new_value=auth_equipment,
                            )
                        )

                table_row.extend([id_colored, name_colored, equip_colored])
            else:
                # Missing from this provider
                missing_id = color_text("TBD", False, True, False)
                missing_name = (
                    color_text(auth_name, False, True, False) if auth_name else ""
                )
                missing_equip = (
                    color_text(auth_equipment, False, True, False)
                    if auth_equipment
                    else ""
                )

                table_row.extend([missing_id, missing_name, missing_equip])

                # Record that this activity should be added to this provider
                if auth_name:  # Only suggest adding if there's a name
                    all_changes.append(
                        ActivityChange(
                            change_type=ChangeType.ADD_ACTIVITY,
                            provider=provider,
                            activity_id=str(auth_activity["id"]),
                            new_value=auth_name,
                            source_provider=auth_provider,
                        )
                    )

        # Add distance
        table_row.append(f"{auth_activity['distance']:.2f}")
        table.append(table_row)

    # Build headers
    headers = ["Start"]
    for provider in provider_list:
        headers.extend(
            [
                f"{provider.title()} ID",
                f"{provider.title()} Name",
                f"{provider.title()} Equip",
            ]
        )
    headers.append("Distance (mi)")

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
    else:
        print("\nNo changes needed - all activities are synchronized!")
