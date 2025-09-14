# Fitler

Fitler is a Python toolkit for aggregating, syncing, and analyzing your fitness activity data from multiple sources (Strava, RideWithGPS, spreadsheets, and local files). It is designed to be self-contained, non-destructive, and extensible.

🌐 **Website**: [fitler.net](https://fitler.net)  
📦 **PyPI**: [pypi.org/project/fitler](https://pypi.org/project/fitler/)  
📚 **Source**: [github.com/ckdake/fitler](https://github.com/ckdake/fitler)

[CAUTION: This is under active development. Do not use it without reading every line of code!]

[![black](https://github.com/ckdake/fitler/actions/workflows/black.yml/badge.svg)](https://github.com/ckdake/fitler/actions/workflows/black.yml)
[![flake8](https://github.com/ckdake/fitler/actions/workflows/flake8.yml/badge.svg)](https://github.com/ckdake/fitler/actions/workflows/flake8.yml)
[![mypy](https://github.com/ckdake/fitler/actions/workflows/mypy.yml/badge.svg)](https://github.com/ckdake/fitler/actions/workflows/mypy.yml)
[![pylint](https://github.com/ckdake/fitler/actions/workflows/pylint.yml/badge.svg)](https://github.com/ckdake/fitler/actions/workflows/pylint.yml)
[![pytest](https://github.com/ckdake/fitler/actions/workflows/pytest.yml/badge.svg)](https://github.com/ckdake/fitler/actions/workflows/pytest.yml)

---

## Features

- Parse and import activity files (`.fit`, `.tcx`, `.gpx`, and compressed variants)
- Integrate with Strava and RideWithGPS APIs
- Store and manage activity metadata in a local SQLite database
- Command-line interface for authentication and future commands
- Modular provider and file format architecture for easy extension

---

## Setup & Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/ckdake/fitler.git
    cd fitler
    ```

2. **(Optional) Open in VS Code Dev Container:**  
   If using VS Code, open the folder and let the devcontainer boot.

3. **Install dependencies:**
    ```sh
    pip install .
    ```

    Or for development:
    ```sh
    pip install -e .
    ```

4. **Set up environment variables:**
   Create a `.env` file in the project root with the following variables:
   ```sh
   # Strava API credentials (required for Strava integration, generate with the auth-strava command)
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   STRAVA_ACCESS_TOKEN=your_access_token
   STRAVA_REFRESH_TOKEN=your_refresh_token
   STRAVA_TOKEN_EXPIRES=token_expiration_timestamp

   # RideWithGPS credentials (required for RWGPS integration)
   RIDEWITHGPS_EMAIL=your_email
   RIDEWITHGPS_PASSWORD=your_password
   RIDEWITHGPS_KEY=your_api_key

   # Garmin Connect credentials (required for Garmin integration)
   GARMIN_EMAIL=your_email
   GARMINTOKENS=~/.garminconnect
   ```
   Note: You can get Strava API credentials by creating an application at https://www.strava.com/settings/api,
   RideWithGPS credentials at https://ridewithgps.com/api, and Garmin Connect credentials by using your 
   existing Garmin Connect account.

5. **Prepare your data:**
    - Place your exported Strava activity files in a folder such as `export_12345/` in the repo root.
    - If you're not using Strava export, place your files in `export_12345/activities/` in the repo root.
    - (Optional) Place your exercise spreadsheet at `~/Documents/exerciselog.xlsx`.

---

## Authenticating with Strava

To use Strava API features, you need to authenticate and get an access token.

1. **Set your Strava API credentials as environment variables:**
    ```sh
    export STRAVA_CLIENT_ID=your_client_id
    export STRAVA_CLIENT_SECRET=your_client_secret
    ```

2. **Run the Strava authentication command:**
    ```sh
    python -m fitler auth-strava
    ```

    This will guide you through the OAuth process and print an access token.  
    Set it in your environment:
    ```sh
    export STRAVA_ACCESS_TOKEN=your_access_token
    ```

---

## Authenticating with Garmin Connect

To use Garmin Connect API features, you need to authenticate and store OAuth tokens.

1. **Set your Garmin Connect credentials as environment variables (optional):**
    ```sh
    export GARMIN_EMAIL=your_email
    export GARMINTOKENS=~/.garminconnect
    ```

2. **Run the Garmin authentication command:**
    ```sh
    python -m fitler auth-garmin
    ```

    This will prompt for your email and password, handle any required MFA, and automatically 
    generate and store OAuth tokens that are valid for about a year. The tokens will be reused 
    automatically for future API calls.

---

## Running Fitler

You can use the CLI for various commands:

```sh
python -m fitler --help
python -m fitler configure
python -m fitler auth-strava
python -m fitler auth-garmin
python -m fitler pull --date 2025-08
python -m fitler sync-month 2025-08
python -m fitler reset --date 2025-08
```

- `configure` – Set up paths and API credentials.
- `auth-strava` – Authenticate with Strava and get an access token.
- `sync` – Sync and match activities from all sources.
- `help` – Show usage and documentation.

You can also use the Python API in your own scripts to process files, sync with providers, or analyze your data.

---

## Running Tests

Fitler uses [pytest](https://pytest.org/) for testing. To run all tests:

```sh
python -m pytest --cov=fitler --cov-report=term-missing -v
```

Test files are in the `tests/` directory and mirror the package structure.

---

## Packaging & Publishing to PyPI

To prepare and publish the package:

1. **Update version and metadata in `setup.py` and `setup.cfg`.**
2. **Build the package:**
    ```sh
    python -m build
    ```
3. **Upload to PyPI (requires `twine`):**
    ```sh
    twine upload dist/*
    ```

---

## Contributing

PRs and issues are welcome! See the TODO section in this README for ideas and next steps.

---

## Development

This is a monorepo containing both the Python package and the static website.

### Repository Structure
```
fitler/
├── fitler/          # Python package source
├── tests/           # Python tests  
├── site/            # Static website source
│   ├── src/         # Website source files
│   ├── scripts/     # Build scripts
│   └── dist/        # Built website (generated)
├── pyproject.toml   # Python package config
└── README.md        # This file (also used for website)
```

### Development Setup

The devcontainer includes both Python and Node.js environments:

```sh
# After starting the devcontainer, dependencies are automatically installed

# For Python development:
python -m pytest                    # Run tests
python -m fitler --help            # Run the CLI

# For website development:  
cd site
npm run dev                         # Start development server (localhost:3000)
npm run build                      # Build for production
```

### Website Development

The website automatically includes content from the main README.md file. To develop:

1. Start the development server: `cd site && npm run dev`
2. Edit files in `site/src/` 
3. The site rebuilds automatically with your changes
4. When satisfied, run `npm run build` to generate the production site

The website is automatically deployed to [fitler.net](https://fitler.net) when changes are pushed to the main branch.

---

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). See the LICENSE file for details.

---

## Getting things back out into spreadsheet

    sqlite3 metadata.sqlite3
    .headers on
    .mode csv
    .output metadata.csv
    SELECT date,activity_type,location_name,city,state,temperature,equipment,duration_hms,max_speed,avg_heart_rate,max_heart_rate,calories,max_elevation,total_elevation_gain,with_names,avg_cadence,strava_id,garmin_id,ridewithgps_id,notes from ActivityMetadata where source="Main";
    .quit

## TODO

    * Next month to fix:  `python -m fitler sync-month 2024-03`
    * File provider manually fixed, go through other providers and manually fix them to work the ~same way. make sure we're not making API calls if the month is synced.
    * Fix strava gear matching to work for running shoes.
    * Fix "create" in providers to create_from_activity, and get all that out of sync_month
    * Write some tests...
    * Get everything out of gpx files: https://pypi.org/project/gpxpy/  (basics are in, need to fill out metadata, add more fields to db!)
    * Get everything out of tcx files: https://pypi.org/project/python-tcxparser/ (basics are in, need to fill out metadata, add more fields to db!) 
    * Get everything out of fit files: https://github.com/dtcooper/python-fitparse/ (basics are in, need to fill out metadata, add more fields to db!)
    * Get everything out of KML files: https://pypi.org/project/pykml/
    * Get everything out of a spreadsheet with headers: https://pypi.org/project/openpyxl/ (basics are in, work better with headers)

    * Output as all fit (lib already included)
    * Output as all tcx (lib already included)
    * Output as all gpx (lib already included)
    * Output as all kml (lib already included)
    * Output as all geojson: https://pypi.org/project/geojson/ 

    * Load files from S3 bucket or somewhere else instead of local: https://pypi.org/project/boto3/ 

    * What is in TrainingPeaks?
    * What is in Wandrer.earth?
    * What about the weather?
    * What about choochoo?
    * What else?

    * switch to fitdecode
