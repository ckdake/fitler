"""Simple Flask web application to view Fitler configuration and database status."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template

# Get the directory where this script is located
app_dir = Path(__file__).parent
app = Flask(__name__, template_folder=str(app_dir / "templates"))

# Look for config file in current directory, then parent directory
CONFIG_PATH = Path("fitler_config.json")
if not CONFIG_PATH.exists():
    CONFIG_PATH = Path("../fitler_config.json")


def load_fitler_config() -> dict[str, Any]:
    """Load Fitler configuration from fitler_config.json."""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "fitler_config.json not found"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}


def get_database_info(db_path: str) -> dict[str, Any]:
    """Get basic information about the SQLite database."""
    if not os.path.exists(db_path):
        return {"error": "Database file not found", "path": db_path}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get database file size
        file_size = os.path.getsize(db_path)

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        # Get row counts for each table
        table_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            table_counts[table] = cursor.fetchone()[0]

        conn.close()

        return {
            "path": db_path,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "tables": table_counts,
            "total_tables": len(tables),
        }
    except sqlite3.Error as e:
        return {"error": f"Database error: {e}", "path": db_path}


@app.route("/")
def index():
    """Main dashboard page."""
    config = load_fitler_config()

    db_info = {}
    if "metadata_db" in config and not config.get("error"):
        db_path = config["metadata_db"]
        db_info = get_database_info(db_path)

    return render_template("index.html", config=config, db_info=db_info)


@app.route("/api/config")
def api_config():
    """API endpoint for configuration data."""
    return jsonify(load_fitler_config())


@app.route("/api/database")
def api_database():
    """API endpoint for database information."""
    config = load_fitler_config()
    if "metadata_db" in config and not config.get("error"):
        db_path = config["metadata_db"]
        return jsonify(get_database_info(db_path))
    return jsonify({"error": "No database configured or config error"})


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "app": "fitler-web"})


if __name__ == "__main__":
    print("🚀 Starting Fitler Web App...")

    # Test that everything works before starting server
    print("� Testing configuration...")
    config = load_fitler_config()
    if config.get("error"):
        print(f"❌ Config error: {config['error']}")
        exit(1)
    else:
        print(f"✅ Config loaded: {config.get('home_timezone')}")

    print("📋 Testing template rendering...")
    with app.test_client() as client:
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Template rendering works")
        else:
            print("❌ Template rendering failed")
            exit(1)

    print("�📍 Server starting at: http://localhost:5000")
    print("🔧 Dashboard: http://localhost:5000")
    print("🔧 Config API: http://localhost:5000/api/config")
    print("💾 Database API: http://localhost:5000/api/database")
    print("❤️  Health Check: http://localhost:5000/health")
    print("\nPress Ctrl+C to stop")

    try:
        app.run(debug=False, host="127.0.0.1", port=5000, threaded=True)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        exit(1)
