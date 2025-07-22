import pytest
from unittest.mock import patch, MagicMock
from fitler.providers.spreadsheet import SpreadsheetProvider
from fitler.activity import Activity
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


@patch("fitler.providers.spreadsheet.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.Path")
@pytest.mark.skip(
    reason="Spreadsheet provider tests need updating for new pull_activities API"
)
def test_fetch_activities(mock_path, mock_load_workbook, mock_sheet):
    # This test needs to be updated to use pull_activities(date_filter) instead of fetch_activities()
    # and to properly mock the spreadsheet structure and database operations
    pass


@patch("fitler.providers.spreadsheet.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.Path")
def test_get_activity_by_id(mock_path, mock_load_workbook, mock_sheet):
    mock_wb = MagicMock()
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider("fake.xlsx")
    activity = provider.get_activity_by_id("2")
    assert isinstance(activity, Activity)
    assert activity.equipment == "Bike"
    assert activity.spreadsheet_id == 2


@patch("fitler.providers.spreadsheet.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.Path")
def test_create_activity(mock_path, mock_load_workbook):
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider("fake.xlsx")
    activity = Activity(
        start_time="2024-06-02",
        activity_type="Run",
        equipment="Shoes",
        notes="Test run",
    )
    mock_sheet.max_row = 3
    result = provider.create_activity(activity)
    mock_sheet.append.assert_called_once()
    mock_wb.save.assert_called_once()
    assert result == "3"


@patch("fitler.providers.spreadsheet.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.Path")
def test_set_gear(mock_path, mock_load_workbook):
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_sheet.max_row = 3
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider("fake.xlsx")
    result = provider.set_gear("NewBike", "2")
    mock_sheet.cell.assert_called_with(row=2, column=8, value="NewBike")
    mock_wb.save.assert_called_once()
    assert result is True


@patch("fitler.providers.spreadsheet.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.Path")
def test_update_activity(mock_path, mock_load_workbook):
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_sheet.max_row = 3
    mock_wb.active = mock_sheet
    mock_load_workbook.return_value = mock_wb
    mock_path.return_value = "fake.xlsx"

    provider = SpreadsheetProvider("fake.xlsx")
    activity = Activity(
        start_time="2024-06-03",
        activity_type="Swim",
        equipment="Goggles",
        notes="Test swim",
    )
    result = provider.update_activity("2", activity)
    assert result is True
    assert mock_sheet.cell.call_count >= 1
    mock_wb.save.assert_called_once()


@patch("fitler.providers.spreadsheet.openpyxl.load_workbook")
@patch("fitler.providers.spreadsheet.Path")
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

    provider = SpreadsheetProvider("fake.xlsx")
    gear = provider.get_gear()
    assert gear == {"Bike": "Bike", "Shoes": "Shoes"}
