import os
import json
import tempfile

import fitler.commands.configure as configure


def test_run_creates_config_file(monkeypatch):
    """Test that configure.run() prompts for input and creates a config file."""

    # Prepare fake user input for all prompts
    inputs = iter(
        [
            "/tmp/fake_spreadsheet.xlsx",
            "./fake_glob/*",
            "US/Pacific",  # Home timezone
            "spreadsheet,strava,ridewithgps",  # Provider priority
            "y",  # Debug mode
        ]
    )
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
        assert config["home_timezone"] == "US/Pacific"
        assert config["provider_priority"] == "spreadsheet,strava,ridewithgps"
        assert config["debug"] == True
