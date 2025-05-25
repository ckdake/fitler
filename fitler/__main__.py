import argparse


def main():
    parser = argparse.ArgumentParser(description="Fitler CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "auth-strava", help="Authenticate with Strava and get an access token"
    )
    subparsers.add_parser("configure", help="Configure Fitler for your environment")
    subparsers.add_parser("sync", help="Sync and match activities from all sources")
    subparsers.add_parser("help", help="Show usage and documentation")

    args = parser.parse_args()

    if args.command == "auth-strava":
        from fitler.commands.auth_strava import run

        run()
    elif args.command == "configure":
        from fitler.commands.configure import run

        run()
    elif args.command == "sync":
        from fitler.commands.sync_all import run

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
    sync          Sync and match activities from all sources
    help          Show this help and usage documentation

Setup:
    1. Run 'python -m fitler configure' to set up paths and API credentials.
    2. Authenticate with Strava using 'python -m fitler auth-strava'.
    3. Sync your activities with 'python -m fitler sync'.

See README.md for more details.
"""
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
