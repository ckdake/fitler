# pylint: disable=import-outside-toplevel
"""Main entry point for the Fitler CLI.

This module provides the command-line interface for Fitler, allowing users to
authenticate with Strava, configure their environment, sync activities, and
access help/documentation.
"""

import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    """Main function for the Fitler CLI."""
    parser = argparse.ArgumentParser(description="Fitler CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "auth-strava", help="Authenticate with Strava and get an access token"
    )
    subparsers.add_parser("configure", help="Configure Fitler for your environment")
    subparsers.add_parser(
        "migrate",
        help="Initialize or upgrade the database. Run this after installation or updates.",
    )
    show_month_parser = subparsers.add_parser(
        "show-month",
        help="Show all activities for a given month (YYYY-MM) from all sources",
    )
    show_month_parser.add_argument(
        "year_month", type=str, help="Year and month in YYYY-MM format"
    )
    sync_month_parser = subparsers.add_parser(
        "sync-month",
        help="Correlate and show all activities for a given month (YYYY-MM) across all sources, dry run",
    )
    sync_month_parser.add_argument(
        "year_month", type=str, help="Year and month in YYYY-MM format"
    )
    subparsers.add_parser("help", help="Show usage and documentation")

    args = parser.parse_args()

    if args.command == "auth-strava":
        from fitler.commands.auth_strava import run

        run()
    elif args.command == "configure":
        from fitler.commands.configure import run

        run()
    elif args.command == "show-month":
        from fitler.commands.show_month import run

        run(args.year_month)
    elif args.command == "sync-month":
        from fitler.commands.sync_month import run

        run(args.year_month)
    elif args.command == "migrate":
        from fitler.commands.migrate import run

        run()
    elif args.command == "help" or args.command is None:
        print(
            """
Fitler - Aggregate, sync, and analyze your fitness activity data.

Usage:
    python -m fitler <command>

Commands:
    auth-strava   Authenticate with Strava and get an access token
    configure     Configure Fitler for your environment (paths, API keys, etc)
    show-month    Show all activities for a given month (YYYY-MM) from all sources
    sync-month    Correlate and show all activities for a given month (YYYY-MM) across all sources, dry run
    help          Show this help and usage documentation

Setup:
    1. Run 'python -m fitler migrate' to initialize the database.
    2. Run 'python -m fitler configure' to set up paths and API credentials.
    3. Authenticate with Strava using 'python -m fitler auth-strava'.
    4. Use 'python -m fitler sync-month YYYY-MM' to view activity correlations.

See README.md for more details.
"""
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
