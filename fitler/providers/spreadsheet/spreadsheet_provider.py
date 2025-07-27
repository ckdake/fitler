"""Spreadsheet provider for Fitler.

This module defines the SpreadsheetProvider class, which provides an interface
for interacting with activity data stored in local spreadsheet files.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import openpyxl
from dateutil import parser as dateparser
import datetime

from fitler.providers.base_provider import FitnessProvider
from fitler.provider_sync import ProviderSync
from fitler.providers.spreadsheet.spreadsheet_activity import SpreadsheetActivity
from peewee import DoesNotExist


class SpreadsheetProvider(FitnessProvider):
    def __init__(self, path: str, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        super().__init__(config)
        self.path = path

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "spreadsheet"

    def pull_activities(self, date_filter: Optional[str] = None) -> List[SpreadsheetActivity]:
        """
        Load all activities from spreadsheet into database, then return filtered activities.
        If date_filter is None, returns all activities.
        If date_filter is provided (YYYY-MM), returns only activities from that month.
        """
        # First, load all activities from the spreadsheet file
        all_activities = self.fetch_activities()
        print(f"Found {len(all_activities)} activities in spreadsheet")
        
        persisted_activities = []
        for activity in all_activities:
            try:
                # Check for duplicates based on spreadsheet_id (row number)
                existing = SpreadsheetActivity.get_or_none(
                    SpreadsheetActivity.spreadsheet_id == activity.spreadsheet_id
                )
                if existing:
                    # Update existing activity with fresh data from spreadsheet
                    for attr in ['start_time', 'activity_type', 'location_name', 'city', 'state', 
                                'temperature', 'equipment', 'duration', 'distance', 'max_speed',
                                'avg_heart_rate', 'max_heart_rate', 'calories', 'max_elevation',
                                'total_elevation_gain', 'with_names', 'avg_cadence', 'strava_id',
                                'garmin_id', 'ridewithgps_id', 'notes', 'name', 'source_file',
                                'source_file_type']:
                        if hasattr(activity, attr):
                            setattr(existing, attr, getattr(activity, attr))
                    existing.save()
                    persisted_activities.append(existing)
                else:
                    # Save new activity to database
                    activity.save()
                    persisted_activities.append(activity)
                    
            except Exception as e:
                print(f"Error persisting spreadsheet activity: {e}")
                continue
        
        print(f"Persisted {len(persisted_activities)} spreadsheet activities to database")
        
        # If no date filter, return all persisted activities
        if date_filter is None:
            return persisted_activities
        
        # Filter activities by the requested month
        filtered_activities = []
        year, month = map(int, date_filter.split("-"))
        
        for activity in persisted_activities:
            if hasattr(activity, 'start_time') and activity.start_time:
                try:
                    # Convert timestamp to datetime for comparison
                    dt = datetime.datetime.fromtimestamp(int(activity.start_time))
                    if dt.year == year and dt.month == month:
                        filtered_activities.append(activity)
                except (ValueError, TypeError):
                    continue
        
        print(f"Returning {len(filtered_activities)} activities for {date_filter}")
        return filtered_activities

    def _seconds_to_hms(self, seconds: Optional[float]) -> str:
        if seconds is None:
            return ""
        try:
            seconds = int(round(seconds))
            return str(datetime.timedelta(seconds=seconds))
        except Exception:
            return ""

    def _hms_to_seconds(self, hms: Optional[str]) -> Optional[float]:
        if not hms:
            return None
        # Accept numeric types directly
        if isinstance(hms, (int, float)):
            return float(hms)
        try:
            import decimal

            if isinstance(hms, decimal.Decimal):
                return float(hms)
        except ImportError:
            pass
        # Accept string types only
        if not isinstance(hms, str):
            return None
        # Ignore openpyxl types that are not string or numeric
        if hasattr(hms, "value") or hasattr(hms, "is_date"):
            return None
        try:
            t = datetime.datetime.strptime(hms, "%H:%M:%S")
            return t.hour * 3600 + t.minute * 60 + t.second
        except Exception:
            try:
                # Try MM:SS
                t = datetime.datetime.strptime(hms, "%M:%S")
                return t.minute * 60 + t.second
            except Exception:
                return None

    def _parse_spreadsheet_datetime(self, dt_val):
        # Spreadsheet times are in local time
        if not dt_val:
            return None
        # Try to parse as datetime
        dt = None
        try:
            dt = dateparser.parse(str(dt_val))
        except Exception:
            return None
        # Attach local timezone if naive
        if dt and dt.tzinfo is None:
            # Use the system's local timezone
            dt = dt.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
        return dt

    def _convert_to_gmt_timestamp(self, dt_val):
        """Convert a YYYY-MM-DD or datetime string to a GMT Unix timestamp.
        Dates from spreadsheet are assumed to be in the configured home timezone."""
        if not dt_val:
            return None
        try:
            # Import here to avoid circular imports
            from pathlib import Path
            import json
            from zoneinfo import ZoneInfo

            # Get home timezone from config
            config_path = Path("fitler_config.json")
            with open(config_path) as f:
                config = json.load(f)
            home_tz = ZoneInfo(config.get("home_timezone", "US/Eastern"))

            # Parse the date string (assumes home timezone)
            dt = dateparser.parse(str(dt_val))
            if dt and dt.tzinfo is None:
                # If no timezone, use configured home timezone
                dt = dt.replace(tzinfo=home_tz)
            # Convert to GMT/UTC and return Unix timestamp
            utc_dt = dt.astimezone(datetime.timezone.utc)
            return str(int(utc_dt.timestamp()))
        except Exception:
            return None

    def fetch_activities(self) -> List[SpreadsheetActivity]:
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        if sheet is None:
            return []

        activities: List[SpreadsheetActivity] = []
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                continue  # Skip header row
            activity_kwargs: Dict[str, Any] = {}
            # Convert date to GMT timestamp
            start_time = self._convert_to_gmt_timestamp(row[0])
            activity_kwargs["start_time"] = start_time

            if row[1]:
                activity_kwargs["activity_type"] = row[1]
            if row[2]:
                activity_kwargs["location_name"] = row[2]
            if row[3]:
                activity_kwargs["city"] = row[3]
            if row[4]:
                activity_kwargs["state"] = row[4]
            if row[5]:
                activity_kwargs["temperature"] = row[5]
            if row[6]:
                activity_kwargs["equipment"] = row[6]
            # duration_hms is stored as HH:MM:SS, but we want .duration in seconds
            if row[7]:
                try:
                    activity_kwargs["duration"] = self._hms_to_seconds(str(row[7]))
                except (ValueError, TypeError):
                    pass
            if row[8]:
                activity_kwargs["distance"] = row[8]
            if row[9]:
                activity_kwargs["max_speed"] = row[9]
            if row[10]:
                activity_kwargs["avg_heart_rate"] = row[10]
            if row[11]:
                activity_kwargs["max_heart_rate"] = row[11]
            if row[12]:
                activity_kwargs["calories"] = row[12]
            if row[13]:
                activity_kwargs["max_elevation"] = row[13]
            if row[14]:
                activity_kwargs["total_elevation_gain"] = row[14]
            if row[15]:
                activity_kwargs["with_names"] = row[15]
            if row[16]:
                activity_kwargs["avg_cadence"] = row[16]
            if row[17]:
                activity_kwargs["strava_id"] = row[17]
            if row[18]:
                activity_kwargs["garmin_id"] = row[18]
            if row[19]:
                activity_kwargs["ridewithgps_id"] = row[19]
            if row[20]:
                activity_kwargs["notes"] = row[20]
                # Use notes field as name if not empty
                activity_kwargs["name"] = row[20]
            activity_kwargs["source_file"] = str(xlsx_file)
            activity_kwargs["source_file_type"] = "spreadsheet"
            activity_kwargs["spreadsheet_id"] = i + 1
            activities.append(SpreadsheetActivity(**activity_kwargs))
        return activities

    def fetch_activities_for_month(self, year_month: str) -> List[SpreadsheetActivity]:
        """
        Return activities for the given year_month (YYYY-MM).
        """
        all_activities = self.fetch_activities()
        filtered = []
        for act in all_activities:
            start_time = getattr(act, "start_time", None)
            if start_time:
                try:
                    # Convert GMT timestamp to local time for comparison
                    dt = datetime.datetime.fromtimestamp(int(start_time))
                    date_str = dt.strftime("%Y-%m")
                    if date_str == year_month:
                        filtered.append(act)
                except (ValueError, TypeError):
                    continue
        return filtered

    def get_activity_by_id(self, activity_id: str) -> Optional[SpreadsheetActivity]:
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active
        
        if sheet is None:
            return None

        row_idx = int(activity_id)
        if row_idx <= 1 or row_idx > sheet.max_row:
            return None

        row = [cell.value for cell in sheet[row_idx]]
        activity_kwargs: Dict[str, Any] = {}
        start_time = self._convert_to_gmt_timestamp(row[0]) if row[0] else None
        activity_kwargs["start_time"] = start_time
        if row[1]:
            activity_kwargs["activity_type"] = row[1]
        if row[2]:
            activity_kwargs["location_name"] = row[2]
        if row[3]:
            activity_kwargs["city"] = row[3]
        if row[4]:
            activity_kwargs["state"] = row[4]
        if row[5]:
            activity_kwargs["temperature"] = row[5]
        if row[6]:
            activity_kwargs["equipment"] = row[6]
        if row[7]:
            activity_kwargs["duration"] = self._hms_to_seconds(str(row[7]))
        if row[8]:
            activity_kwargs["distance"] = row[8]
        if row[9]:
            activity_kwargs["max_speed"] = row[9]
        if row[10]:
            activity_kwargs["avg_heart_rate"] = row[10]
        if row[11]:
            activity_kwargs["max_heart_rate"] = row[11]
        if row[12]:
            activity_kwargs["calories"] = row[12]
        if row[13]:
            activity_kwargs["max_elevation"] = row[13]
        if row[14]:
            activity_kwargs["total_elevation_gain"] = row[14]
        if row[15]:
            activity_kwargs["with_names"] = row[15]
        if row[16]:
            activity_kwargs["avg_cadence"] = row[16]
        if row[17]:
            activity_kwargs["strava_id"] = row[17]
        if row[18]:
            activity_kwargs["garmin_id"] = row[18]
        if row[19]:
            activity_kwargs["ridewithgps_id"] = row[19]
        if row[20]:
            activity_kwargs["notes"] = row[20]
        activity_kwargs["source_file"] = str(xlsx_file)
        activity_kwargs["source_file_type"] = "spreadsheet"
        activity_kwargs["spreadsheet_id"] = row_idx
        return SpreadsheetActivity(**activity_kwargs)



    def update_activity(self, activity_data: Dict[str, Any]) -> Any:
        """Update an existing SpreadsheetActivity with new data."""
        try:
            activity_id = activity_data.get("spreadsheet_id")
            if not activity_id:
                return None
            activity = SpreadsheetActivity.get(SpreadsheetActivity.spreadsheet_id == activity_id)
            for key, value in activity_data.items():
                if key != "spreadsheet_id":  # Don't update the ID itself
                    setattr(activity, key, value)
            activity.save()
            return activity
        except Exception:
            return None

    def create_activity(self, activity_data: Dict[str, Any]) -> str:
        """Create a new activity in the spreadsheet from activity data."""
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        # Get the next row number
        next_row = sheet.max_row + 1
        
        # Prepare the row data
        row = [
            activity_data.get("start_time", ""),
            activity_data.get("activity_type", ""),
            activity_data.get("location_name", ""),
            activity_data.get("city", ""),
            activity_data.get("state", ""),
            activity_data.get("temperature", ""),
            activity_data.get("equipment", ""),
            self._seconds_to_hms(activity_data.get("duration", None)),
            activity_data.get("distance", ""),
            activity_data.get("max_speed", ""),
            activity_data.get("avg_heart_rate", ""),
            activity_data.get("max_heart_rate", ""),
            activity_data.get("calories", ""),
            activity_data.get("max_elevation", ""),
            activity_data.get("total_elevation_gain", ""),
            activity_data.get("with_names", ""),
            activity_data.get("avg_cadence", ""),
            activity_data.get("strava_id", ""),
            activity_data.get("garmin_id", ""),
            activity_data.get("ridewithgps_id", ""),
            activity_data.get("notes", ""),
        ]
        
        sheet.append(row)
        wb_obj.save(xlsx_file)
        return str(next_row)

    def get_gear(self) -> Dict[str, str]:
        """Fetch gear/equipment from the spreadsheet."""
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active
        
        if sheet is None:
            return {}

        gear_set = set()
        # The equipment column is index 6 (0-based)
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                continue  # Skip header row
            equipment = row[6] if len(row) > 6 else None
            if equipment:
                gear_set.add(str(equipment))
        # Use the equipment name as both key and value
        return {name: name for name in gear_set}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """Set the gear/equipment for a specific activity."""
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active
        
        if sheet is None:
            return False

        row_idx = int(activity_id)
        if row_idx <= 1 or row_idx > sheet.max_row:
            return False

        # Equipment is in column 7 (1-based)
        sheet.cell(row=row_idx, column=7, value=gear_id)
        wb_obj.save(xlsx_file)
        return True
