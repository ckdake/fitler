import os
import json
import tempfile

import fitler.commands.configure as configure

def test_run_creates_config_file(monkeypatch):
    """Test that configure.run() prompts for input and creates a config file."""

    # Prepare fake user input for all prompts
    inputs = iter([
        "/tmp/fake_spreadsheet.xlsx",
        "./fake_glob/*",
        "12345",  # Strava Client ID
        "secret",  # Strava Client Secret
        "user@example.com",  # RideWithGPS Email
        "password",  # RideWithGPS Password
        "apikey",    # RideWithGPS API Key
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # Use a temp directory for config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "fitler_config.json")
        monkeypatch.setattr("os.path.abspath", lambda path: config_path)

        configure.run()

        assert os.path.exists(config_path)
        with open(config_path) as f:
            config = json.load(f)
        assert config["spreadsheet_path"] == "/tmp/fake_spreadsheet.xlsx"
        assert config["activity_file_glob"] == "./fake_glob/*"
        assert config["strava_client_id"] == "12345"
        assert config["strava_client_secret"] == "secret"
        assert config["ridewithgps_email"] == "user@example.com"
        assert config["ridewithgps_password"] == "password"
        assert config["ridewithgps_key"] == "apikey"