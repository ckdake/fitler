import pytest
from unittest.mock import patch, MagicMock
from fitler.providers.spreadsheet import SpreadsheetProvider
from fitler.activity import Activity
from fitler.providers.spreadsheet.spreadsheet_activity import SpreadsheetActivity
from fitler.providers.base_provider_activity import BaseProviderActivity
import datetime


def seconds_to_hms(seconds):
    if seconds is None:
        return ""
    return str(datetime.timedelta(seconds=int(round(seconds))))


@pytest.fixture
def mock_sheet():
    # Simulate a sheet with a header and one data row
    header = [
        "start_time",
        "activity_type",
        "location_name",
        "city",
        "state",
        "temperature",
        "equipment",
        "duration_hms",
        "distance",
        "max_speed",
        "avg_heart_rate",
        "max_heart_rate",
        "calories",
        "max_elevation",
        "total_elevation_gain",
        "with_names",
        "avg_cadence",
        "strava_id",
        "garmin_id",
        "ridewithgps_id",
        "notes",
    ]
    data_row = [
        "2024-06-01T10:00:00Z",
        "Ride",
        "Park",
        "Atlanta",
        "GA",
        72,
        "Bike",
        "1:00:00",
        25.0,
        30.0,
        140,
        160,
        500,
        300,
        1000,
        "Alice,Bob",
        85,
        123,
        456,
        789,
        "Nice ride",
    ]
    # iter_rows returns an iterator of tuples, first header, then data
    return MagicMock(
        iter_rows=MagicMock(return_value=[header, data_row]),
        max_row=2,
        __getitem__=lambda self, idx: [MagicMock(value=v) for v in data_row],
    )


@patch("fitler.providers.spreadsheet.spreadsheet_provider.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.spreadsheet_provider.Path")
def test_pull_activities(mock_path, mock_load_workbook, mock_sheet):
    """Test pull_activities method with proper database mocking."""
    mock_wb = MagicMock()
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    # Mock that no existing activities are found (new activities)
    with patch(
        "fitler.providers.spreadsheet.spreadsheet_activity.SpreadsheetActivity.get_or_none"
    ) as mock_get_or_none:
        mock_get_or_none.return_value = None

        provider = SpreadsheetProvider(
            "fake.xlsx", config={"home_timezone": "US/Eastern", "test_mode": True}
        )
        activities = provider.pull_activities()

        # Should return list of SpreadsheetActivity objects
        assert isinstance(activities, list)
        assert len(activities) == 1  # One data row from mock_sheet
        assert isinstance(activities[0], SpreadsheetActivity)
        assert activities[0].equipment == "Bike"
        assert activities[0].spreadsheet_id == "1"  # Row 1 (first data row, as string)


@patch("fitler.providers.spreadsheet.spreadsheet_provider.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.spreadsheet_provider.Path")
def test_get_activity_by_id(mock_path, mock_load_workbook, mock_sheet):
    mock_wb = MagicMock()
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider(
        "fake.xlsx", config={"home_timezone": "US/Eastern", "test_mode": True}
    )
    # Insert a mock activity into the test DB
    from fitler.providers.spreadsheet.spreadsheet_activity import SpreadsheetActivity

    SpreadsheetActivity.create(
        start_time="2024-06-01T10:00:00Z",
        activity_type="Ride",
        spreadsheet_id=2,
        equipment="Bike",
    )
    activity = provider.get_activity_by_id("2")
    assert isinstance(activity, BaseProviderActivity)
    assert activity.equipment == "Bike"
    assert activity.spreadsheet_id == "2"


@patch("fitler.providers.spreadsheet.spreadsheet_provider.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.spreadsheet_provider.Path")
def test_create_activity(mock_path, mock_load_workbook):
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider(
        "fake.xlsx", config={"home_timezone": "US/Eastern", "test_mode": True}
    )
    # Test with dictionary data (no Activity objects in providers!)
    activity_data = {
        "start_time": "2024-06-02",
        "activity_type": "Run",
        "spreadsheet_id": 2,
        "equipment": "Shoes",
        "notes": "Test run",
    }
    mock_sheet.max_row = 2
    result = provider.create_activity(activity_data)
    mock_sheet.append.assert_called_once()
    mock_wb.save.assert_called_once()
    assert result == "3"


@patch("fitler.providers.spreadsheet.spreadsheet_provider.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.spreadsheet_provider.Path")
def test_set_gear(mock_path, mock_load_workbook):
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_sheet.max_row = 2
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider(
        "fake.xlsx", config={"home_timezone": "US/Eastern", "test_mode": True}
    )
    result = provider.set_gear("NewBike", "2")
    mock_sheet.cell.assert_called_with(row=2, column=7, value="NewBike")
    mock_wb.save.assert_called_once()
    assert result is True


@patch("fitler.providers.spreadsheet.spreadsheet_activity.SpreadsheetActivity.get")
def test_update_activity(mock_get):
    """Test updating activity via provider update_activity method."""
    mock_activity = MagicMock()
    mock_get.return_value = mock_activity

    provider = SpreadsheetProvider(
        "fake.xlsx", config={"home_timezone": "US/Eastern", "test_mode": True}
    )

    # Test with dictionary data (no Activity objects in providers!)
    activity_data = {
        "start_time": "2024-06-02",
        "activity_type": "Run",
        "spreadsheet_id": 2,
        "equipment": "Shoes",
        "notes": "Test run",
    }

    result = provider.update_activity(activity_data)

    # Verify the activity was retrieved, updated, and saved
    mock_get.assert_called_once()
    mock_activity.save.assert_called_once()
    assert result == mock_activity


@patch("fitler.providers.spreadsheet.spreadsheet_provider.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.spreadsheet_provider.Path")
def test_get_gear(mock_path, mock_load_workbook, mock_sheet):
    mock_wb = MagicMock()
    # Simulate two rows with different equipment
    header = [
        "start_time",
        "activity_type",
        "location_name",
        "city",
        "state",
        "temperature",
        "equipment",
        "duration_hms",
        "distance",
        "max_speed",
        "avg_heart_rate",
        "max_heart_rate",
        "calories",
        "max_elevation",
        "total_elevation_gain",
        "with_names",
        "avg_cadence",
        "strava_id",
        "garmin_id",
        "ridewithgps_id",
        "notes",
    ]
    row1 = [
        "2024-06-01T10:00:00Z",
        "Ride",
        "Park",
        "Atlanta",
        "GA",
        72,
        "Bike",
        "1:00:00",
        25.0,
        30.0,
        140,
        160,
        500,
        300,
        1000,
        "Alice,Bob",
        85,
        123,
        456,
        789,
        "Nice ride",
    ]
    row2 = [
        "2024-06-02T10:00:00Z",
        "Run",
        "Trail",
        "Atlanta",
        "GA",
        70,
        "Shoes",
        "0:30:00",
        5.0,
        10.0,
        130,
        150,
        200,
        100,
        300,
        "Bob",
        80,
        124,
        457,
        790,
        "Morning run",
    ]
    mock_sheet = MagicMock(iter_rows=MagicMock(return_value=[header, row1, row2]))
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider(
        "fake.xlsx", config={"home_timezone": "US/Eastern", "test_mode": True}
    )
    gear = provider.get_gear()
    assert gear == {"Bike": "Bike", "Shoes": "Shoes"}


# New tests for config parameter functionality
def test_spreadsheet_provider_with_config():
    """Test that SpreadsheetProvider accepts and stores config parameter."""
    config = {"home_timezone": "US/Pacific", "enabled": True, "path": "/test/path.xlsx"}

    provider = SpreadsheetProvider("/test/path.xlsx", config=config)

    # Test that config is stored
    assert provider.config == config
    assert provider.config["home_timezone"] == "US/Pacific"
    assert provider.config["enabled"] == True


def test_spreadsheet_provider_without_config():
    """Test that SpreadsheetProvider works without config parameter (backward compatibility)."""
    provider = SpreadsheetProvider("/test/path.xlsx")

    # Should have empty config dict
    assert provider.config == {}
    assert provider.path == "/test/path.xlsx"


def test_spreadsheet_provider_with_none_config():
    """Test that SpreadsheetProvider handles None config parameter."""
    provider = SpreadsheetProvider("/test/path.xlsx", config=None)

    # Should have empty config dict when None is passed
    assert provider.config == {}
    assert provider.path == "/test/path.xlsx"


def test_spreadsheet_provider_config_access():
    """Test accessing config values from the provider."""
    config = {
        "home_timezone": "Europe/London",
        "debug": True,
        "custom_setting": "test_value",
    }

    provider = SpreadsheetProvider("/test/path.xlsx", config=config)

    # Test accessing various config values
    assert provider.config.get("home_timezone") == "Europe/London"
    assert provider.config.get("debug") == True
    assert provider.config.get("custom_setting") == "test_value"
    assert provider.config.get("nonexistent", "default") == "default"


@patch("fitler.providers.spreadsheet.spreadsheet_provider.FitnessProvider.__init__")
def test_spreadsheet_provider_calls_super_with_config(mock_super_init):
    """Test that SpreadsheetProvider calls super().__init__(config)."""
    config = {"home_timezone": "US/Pacific", "enabled": True}

    # Make the mock return None to avoid issues
    mock_super_init.return_value = None

    provider = SpreadsheetProvider("/test/path.xlsx", config=config)

    # Verify super().__init__ was called with the config
    mock_super_init.assert_called_once_with(config)


def test_spreadsheet_provider_with_enhanced_config():
    """Test SpreadsheetProvider with enhanced config including home_timezone."""
    enhanced_config = {
        "enabled": True,
        "path": "/test/spreadsheet.xlsx",
        "home_timezone": "America/New_York",
        "debug": False,
    }

    provider = SpreadsheetProvider("/test/spreadsheet.xlsx", config=enhanced_config)

    # Verify all config values are accessible
    assert provider.config["home_timezone"] == "America/New_York"
    assert provider.config["enabled"] == True
    assert provider.config["debug"] == False
    assert provider.path == "/test/spreadsheet.xlsx"


def test_spreadsheet_provider_mimics_core_behavior():
    """Test that SpreadsheetProvider works with config structure from core.py."""
    # Simulate the enhanced_config that core.py creates
    provider_config = {"enabled": True, "path": "/test/spreadsheet.xlsx"}

    # This is what core.py does - creates enhanced_config
    enhanced_config = provider_config.copy()
    enhanced_config["home_timezone"] = "US/Eastern"

    # This is how core.py calls the provider
    provider = SpreadsheetProvider("/test/spreadsheet.xlsx", config=enhanced_config)

    # Verify that the provider has access to both the provider config and home_timezone
    assert provider.config["enabled"] == True
    assert provider.config["path"] == "/test/spreadsheet.xlsx"
    assert provider.config["home_timezone"] == "US/Eastern"
    assert provider.path == "/test/spreadsheet.xlsx"


def test_spreadsheet_provider_timezone_access():
    """Test that provider can access home_timezone for timezone conversion."""
    config = {"home_timezone": "America/Los_Angeles", "enabled": True}
    provider = SpreadsheetProvider("/test/path.xlsx", config=config)

    # Provider should be able to access the timezone setting
    timezone = provider.config.get("home_timezone", "UTC")
    assert timezone == "America/Los_Angeles"

    # This would be useful for timezone conversions in the provider
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(timezone)
    assert str(tz) == "America/Los_Angeles"


def test_convert_to_gmt_timestamp_date_only_eastern():
    """Test _convert_to_gmt_timestamp with date-only string and US/Eastern timezone."""
    from fitler.providers.spreadsheet.spreadsheet_provider import SpreadsheetProvider
    from zoneinfo import ZoneInfo

    # Feb 3, 2025 in US/Eastern should be 2025-02-03 00:00:00-05:00
    # Which is 2025-02-03 05:00:00 UTC
    dt_str = "2025-02-03"  # How this appears in the spreadsheet
    tz = "US/Eastern"  # Where the activity was recorded
    ts = SpreadsheetProvider._convert_to_gmt_timestamp(dt_str, tz)
    assert ts == 1738558800  # 2025-02-03 05:00:00 UTC = 1738568400

    dt_str = "2025-02-03 00:00:00"  # How this appears in the spreadsheet
    tz = "US/Eastern"  # Where the activity was recorded
    ts = SpreadsheetProvider._convert_to_gmt_timestamp(dt_str, tz)
    assert ts == 1738558800  # 2025-02-03 05:00:00 UTC = 1738568400
