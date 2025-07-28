"""Pull command for syncing activities from providers."""

import argparse
from fitler.core import Fitler


def run(args=None):
    """Run the pull command."""
    parser = argparse.ArgumentParser(description="Pull activities from providers")
    parser.add_argument(
        "provider",
        nargs="?",
        choices=[
            "files",
            "strava",
            "ridewithgps",
            "garmin",
            "spreadsheet",
            "stravajson",
        ],
        help="Provider to pull from (if not specified, pulls from all enabled providers)",
    )
    parser.add_argument(
        "--date",
        help="Date filter in YYYY-MM format (if not specified, pulls all activities)",
    )

    parsed_args = parser.parse_args(args)

    with Fitler() as fitler:
        if parsed_args.provider:
            # Pull from specific provider
            provider_instance = _get_provider_instance(fitler, parsed_args.provider)
            if provider_instance:
                print(f"Pulling activities from {parsed_args.provider}...")
                activities = provider_instance.pull_activities(parsed_args.date)
                print(
                    f"Pulled {len(activities)} activities from {parsed_args.provider}"
                )
            else:
                print(
                    f"Provider {parsed_args.provider} not available or not configured"
                )
        else:
            # Pull from all enabled providers
            enabled_provider_names = fitler.enabled_providers
            if not enabled_provider_names:
                print("No providers are enabled. Check your configuration.")
                return

            total_activities = 0
            for provider_name in enabled_provider_names:
                provider_instance = _get_provider_instance(fitler, provider_name)
                if provider_instance:
                    print(f"Pulling activities from {provider_name}...")
                    try:
                        activities = provider_instance.pull_activities(parsed_args.date)
                        count = len(activities)
                        total_activities += count
                        print(f"Pulled {count} activities from {provider_name}")
                    except Exception as e:
                        print(f"Error pulling from {provider_name}: {e}")
                else:
                    print(f"Could not initialize provider: {provider_name}")

            print(f"Total activities pulled: {total_activities}")


def _get_provider_instance(fitler: Fitler, provider_name: str):
    """Get a provider instance by name."""
    if provider_name == "files" or provider_name == "file":
        return fitler.file
    elif provider_name == "strava":
        return fitler.strava
    elif provider_name == "ridewithgps":
        return fitler.ridewithgps
    elif provider_name == "garmin":
        return fitler.garmin
    elif provider_name == "spreadsheet":
        return fitler.spreadsheet
    elif provider_name == "stravajson":
        return fitler.stravajson
    else:
        return None
