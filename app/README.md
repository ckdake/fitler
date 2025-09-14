# Fitler Web App

A simple Flask-based web application for viewing Fitler configuration and database status during local development.

## Features

- 📊 **Dashboard**: View current Fitler configuration
- 🔌 **Provider Status**: See which providers are enabled/disabled
- 💾 **Database Info**: Check SQLite database status and table counts
- 🔗 **API Endpoints**: JSON endpoints for programmatic access

## Quick Start

From the project root directory:

```bash
# Run the development server
./dev.sh
```

The app will be available at: http://localhost:5000

## API Endpoints

- `GET /` - Main dashboard (HTML)
- `GET /api/config` - Configuration data (JSON)
- `GET /api/database` - Database information (JSON)
- `GET /health` - Health check (JSON)

## Development

The web app automatically:
- Reads `fitler_config.json` from the parent directory
- Connects to the configured SQLite database
- Provides real-time status information

## Future Plans

This local development app will eventually be deployed to `app.fitler.net` for remote access to Fitler status and management.

## Requirements

- Python 3.7+
- Flask 3.0+
- Access to `fitler_config.json` and the configured SQLite database

## Structure

```
app/
├── main.py              # Flask application
├── templates/
│   └── index.html       # Dashboard template
└── README.md           # This file
```
