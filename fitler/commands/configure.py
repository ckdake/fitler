import os
import json


def run():
    print("Welcome to Fitler configuration!")
    config = {}

    # Prompt for spreadsheet path
    spreadsheet = input(
        "Path to activity spreadsheet (e.g. /home/vscode/exerciselog.xlsx): "
    ).strip()
    config["spreadsheet_path"] = spreadsheet

    # Prompt for activity file glob
    file_glob = input(
        "Glob for activity file collection (e.g. ./export*/activities/*): "
    ).strip()
    config["activity_file_glob"] = file_glob

    print("\nNote: Strava and RideWithGPS credentials should be set in .env file.")
    print("See README.md for details on setting up provider credentials.\n")

    # Prompt for home timezone
    print("\n--- Timezone Configuration ---")
    print("Common timezones: US/Eastern, US/Central, US/Mountain, US/Pacific")
    timezone = input("Home timezone (default: US/Eastern): ").strip()
    config["home_timezone"] = timezone or "US/Eastern"

    # Prompt for provider priority
    print("\n--- Provider Priority Configuration ---")
    print("This setting controls which provider's data takes precedence when")
    print("there are conflicts in activity names or equipment.")
    print("Available providers: spreadsheet, ridewithgps, strava")
    print("Enter them in order of priority, comma-separated.")
    provider_priority = input("Provider priority (default: spreadsheet,ridewithgps,strava): ").strip()
    config["provider_priority"] = provider_priority or "spreadsheet,ridewithgps,strava"

    # Prompt for debug mode
    debug_input = input("\nEnable debug mode? (y/N): ").strip().lower()
    config["debug"] = debug_input == "y"

    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../fitler_config.json")
    )
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"\nConfiguration saved to {config_path}")
