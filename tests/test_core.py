import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from fitler.core import Fitler, CONFIG_PATH


class TestFitlerCore:
    """Test the core Fitler class functionality."""

    def test_fitler_init_loads_config(self, tmp_path):
        """Test that Fitler initializes and loads config correctly."""
        # Create a temporary config file with new format
        config_data = {
            "home_timezone": "US/Pacific",
            "debug": False,
            "provider_priority": "spreadsheet,strava",
            "providers": {
                "spreadsheet": {
                    "enabled": True,
                    "path": "/tmp/test.xlsx"
                },
                "strava": {
                    "enabled": True
                },
                "file": {
                    "enabled": True,
                    "glob": "./test/*"
                }
            }
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                assert fitler.config["home_timezone"] == "US/Pacific"
                assert fitler.config["debug"] == False
                assert fitler.config["providers"]["spreadsheet"]["path"] == "/tmp/test.xlsx"

    def test_fitler_config_defaults(self, tmp_path):
        """Test that Fitler sets default config values."""
        # Create minimal config
        config_data = {"spreadsheet_path": "/tmp/test.xlsx"}

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # Should set defaults and create providers section for backward compatibility
                assert fitler.config["debug"] == False
                assert (
                    fitler.config["provider_priority"]
                    == "spreadsheet,ridewithgps,strava,garmin"
                )
                assert "providers" in fitler.config
                assert fitler.config["providers"]["spreadsheet"]["enabled"] == True
                assert fitler.config["providers"]["spreadsheet"]["path"] == "/tmp/test.xlsx"

    def test_enabled_providers_empty(self, tmp_path):
        """Test enabled_providers when no providers are enabled."""
        config_data = {
            "providers": {
                "spreadsheet": {"enabled": False},
                "strava": {"enabled": False},
                "ridewithgps": {"enabled": False},
                "garmin": {"enabled": False},
                "file": {"enabled": False},
                "stravajson": {"enabled": False}
            }
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # No providers should be enabled
                assert fitler.enabled_providers == []

    def test_enabled_providers_with_spreadsheet(self, tmp_path):
        """Test enabled_providers when spreadsheet is configured and enabled."""
        config_data = {
            "providers": {
                "spreadsheet": {
                    "enabled": True,
                    "path": "/tmp/test.xlsx"
                },
                "strava": {"enabled": False},
                "ridewithgps": {"enabled": False},
                "garmin": {"enabled": False},
                "file": {"enabled": False},
                "stravajson": {"enabled": False}
            }
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # Should detect spreadsheet provider
                assert "spreadsheet" in fitler.enabled_providers

    @patch.dict(
        os.environ,
        {
            "STRAVA_ACCESS_TOKEN": "test_token",
            "STRAVA_CLIENT_ID": "12345",
            "STRAVA_CLIENT_SECRET": "secret",
        },
    )
    def test_enabled_providers_with_strava_env(self, tmp_path):
        """Test enabled_providers when Strava env vars are set and provider is enabled."""
        config_data = {
            "providers": {
                "spreadsheet": {"enabled": False},
                "strava": {"enabled": True},
                "ridewithgps": {"enabled": False},
                "garmin": {"enabled": False},
                "file": {"enabled": False},
                "stravajson": {"enabled": False}
            }
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # Should detect strava provider due to env vars and enabled config
                assert "strava" in fitler.enabled_providers

    @patch.dict(
        os.environ,
        {
            "STRAVA_ACCESS_TOKEN": "test_token",
            "STRAVA_CLIENT_ID": "12345",
            "STRAVA_CLIENT_SECRET": "secret",
        },
    )
    def test_enabled_providers_with_strava_disabled(self, tmp_path):
        """Test enabled_providers when Strava env vars are set but provider is disabled."""
        config_data = {
            "providers": {
                "spreadsheet": {"enabled": False},
                "strava": {"enabled": False},  # Disabled in config
                "ridewithgps": {"enabled": False},
                "garmin": {"enabled": False},
                "file": {"enabled": False},
                "stravajson": {"enabled": False}
            }
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # Should NOT detect strava provider because it's disabled in config
                assert "strava" not in fitler.enabled_providers

    def test_cleanup_closes_db(self, tmp_path):
        """Test that cleanup properly closes database connection."""
        config_data = {}

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True
                mock_db.close.return_value = None

                fitler = Fitler()
                fitler.cleanup()

                mock_db.close.assert_called_once()

    def test_context_manager(self, tmp_path):
        """Test that Fitler works as a context manager."""
        config_data = {}

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True
                mock_db.close.return_value = None

                with Fitler() as fitler:
                    assert fitler is not None

                # Should have called cleanup
                mock_db.close.assert_called_once()

    def test_pull_activities_error_handling(self, tmp_path):
        """Test that pull_activities handles provider errors gracefully."""
        config_data = {
            "providers": {
                "spreadsheet": {
                    "enabled": True,
                    "path": "/tmp/test.xlsx"
                }
            }
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # Mock a provider that raises an exception
                mock_provider = MagicMock()
                mock_provider.pull_activities.side_effect = Exception("Test error")
                fitler._spreadsheet = mock_provider

                result = fitler.pull_activities("2024-01")

                # Should handle error gracefully and return empty list
                assert result["spreadsheet"] == []

    def test_backward_compatibility_old_config(self, tmp_path):
        """Test that old config format still works with backward compatibility."""
        # Old config format without providers block
        config_data = {
            "spreadsheet_path": "/tmp/test.xlsx",
            "activity_file_glob": "./test/*",
            "home_timezone": "US/Pacific"
        }

        config_file = tmp_path / "fitler_config.json"
        config_file.write_text(json.dumps(config_data))

        with patch("fitler.core.CONFIG_PATH", config_file):
            with patch("fitler.core.db") as mock_db:
                mock_db.connect.return_value = None
                mock_db.is_connection_usable.return_value = True

                fitler = Fitler()

                # Should create providers section automatically
                assert "providers" in fitler.config
                assert fitler.config["providers"]["spreadsheet"]["enabled"] == True
                assert fitler.config["providers"]["spreadsheet"]["path"] == "/tmp/test.xlsx"
                assert fitler.config["providers"]["file"]["enabled"] == True
                assert fitler.config["providers"]["file"]["glob"] == "./test/*"
