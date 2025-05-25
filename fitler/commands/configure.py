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

    # Placeholders for Strava API credentials
    print("\n--- Strava API Credentials ---")
    print("You can fill these in later if you don't have them now.")
    config["strava_client_id"] = (
        input("Strava Client ID: ").strip() or "YOUR_STRAVA_CLIENT_ID"
    )
    config["strava_client_secret"] = (
        input("Strava Client Secret: ").strip() or "YOUR_STRAVA_CLIENT_SECRET"
    )

    # Placeholders for RideWithGPS API credentials
    print("\n--- RideWithGPS API Credentials ---")
    print("You can fill these in later if you don't have them now.")
    config["ridewithgps_email"] = (
        input("RideWithGPS Email: ").strip() or "YOUR_RIDEWITHGPS_EMAIL"
    )
    config["ridewithgps_password"] = (
        input("RideWithGPS Password: ").strip() or "YOUR_RIDEWITHGPS_PASSWORD"
    )
    config["ridewithgps_key"] = (
        input("RideWithGPS API Key: ").strip() or "YOUR_RIDEWITHGPS_API_KEY"
    )

    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../fitler_config.json")
    )
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"\nConfiguration saved to {config_path}")
