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
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from peewee import DoesNotExist


class SpreadsheetProvider(FitnessProvider):
    def __init__(self, path: str):
        self.path = path

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "spreadsheet"

    def pull_activities(self, date_filter: str) -> List[Activity]:
        """
        Sync activities for a given month filter in YYYY-MM format.
        Returns a list of synced Activity objects that have been persisted to the database.
        """
        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if existing_sync:
            # Return activities from database for this month
            try:
                # Query activities that have spreadsheet_id set AND
                # source=spreadsheet for this month
                existing_activities = list(
                    Activity.select().where(
                        (Activity.spreadsheet_id.is_null(False))
                        & (Activity.source == self.provider_name)
                    )
                )

                # Filter by month in Python since date comparison is tricky
                year, month = map(int, date_filter.split("-"))
                filtered_activities = []
                for act in existing_activities:
                    if act.date and act.date.year == year and act.date.month == month:
                        filtered_activities.append(act)

                print(
                    f"Found {len(filtered_activities)} existing activities "
                    f"from database for {self.provider_name}"
                )
                return filtered_activities
            except Exception as e:
                print(f"Error loading existing activities: {e}")
                # Fall through to re-sync

        # Get the raw activity data for the month
        raw_activities = self.fetch_activities_for_month(date_filter)

        # Load config for provider priority
        persisted_activities = []

        for raw_activity in raw_activities:
            # Convert the raw activity data to a dict for update_from_provider
            activity_data = {
                "id": getattr(raw_activity, "spreadsheet_id", None),
                "name": getattr(raw_activity, "name", None)
                or getattr(raw_activity, "notes", None),
                "distance": getattr(raw_activity, "distance", None),
                "equipment": getattr(raw_activity, "equipment", None),
                "activity_type": getattr(raw_activity, "activity_type", None),
                "start_time": getattr(raw_activity, "departed_at", None),
                "location_name": getattr(raw_activity, "location_name", None),
                "city": getattr(raw_activity, "city", None),
                "state": getattr(raw_activity, "state", None),
                "temperature": getattr(raw_activity, "temperature", None),
                "duration": getattr(raw_activity, "duration", None),
                "max_speed": getattr(raw_activity, "max_speed", None),
                "avg_heart_rate": getattr(raw_activity, "avg_heart_rate", None),
                "max_heart_rate": getattr(raw_activity, "max_heart_rate", None),
                "calories": getattr(raw_activity, "calories", None),
                "max_elevation": getattr(raw_activity, "max_elevation", None),
                "total_elevation_gain": getattr(
                    raw_activity, "total_elevation_gain", None
                ),
                "avg_cadence": getattr(raw_activity, "avg_cadence", None),
                "notes": getattr(raw_activity, "notes", None),
                # Include provider IDs from spreadsheet
                "strava_id": getattr(raw_activity, "strava_id", None),
                "garmin_id": getattr(raw_activity, "garmin_id", None),
                "ridewithgps_id": getattr(raw_activity, "ridewithgps_id", None),
                # Set source to this provider
                "source": self.provider_name,
            }

            # Look for existing activity with this spreadsheet_id AND source=spreadsheet
            existing_activity = None
            if activity_data["id"]:
                try:
                    existing_activity = Activity.get(
                        (Activity.spreadsheet_id == activity_data["id"])
                        & (Activity.source == self.provider_name)
                    )
                except DoesNotExist:
                    existing_activity = None

            if existing_activity:
                # Update existing activity
                activity = existing_activity
            else:
                # Create new activity
                activity = Activity()

            # Set the start time if available
            if activity_data.get("start_time"):
                activity.set_start_time(str(activity_data["start_time"]))

            # Set all the fields directly instead of using update_from_provider
            activity.spreadsheet_id = activity_data["id"]
            if activity_data.get("name"):
                activity.name = activity_data["name"]
            if activity_data.get("distance"):
                activity.distance = activity_data["distance"]
            if activity_data.get("equipment"):
                activity.equipment = activity_data["equipment"]
            if activity_data.get("activity_type"):
                activity.activity_type = activity_data["activity_type"]
            if activity_data.get("location_name"):
                activity.location_name = activity_data["location_name"]
            if activity_data.get("city"):
                activity.city = activity_data["city"]
            if activity_data.get("state"):
                activity.state = activity_data["state"]
            if activity_data.get("temperature"):
                activity.temperature = activity_data["temperature"]
            if activity_data.get("duration"):
                # Convert duration seconds to HH:MM:SS format for duration_hms field
                duration_seconds = activity_data["duration"]
                if duration_seconds:
                    hours = int(duration_seconds // 3600)
                    minutes = int((duration_seconds % 3600) // 60)
                    seconds = int(duration_seconds % 60)
                    activity.duration_hms = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if activity_data.get("max_speed"):
                activity.max_speed = activity_data["max_speed"]
            if activity_data.get("avg_heart_rate"):
                activity.avg_heart_rate = activity_data["avg_heart_rate"]
            if activity_data.get("max_heart_rate"):
                activity.max_heart_rate = activity_data["max_heart_rate"]
            if activity_data.get("calories"):
                activity.calories = activity_data["calories"]
            if activity_data.get("max_elevation"):
                activity.max_elevation = activity_data["max_elevation"]
            if activity_data.get("total_elevation_gain"):
                activity.total_elevation_gain = activity_data["total_elevation_gain"]
            if activity_data.get("avg_cadence"):
                activity.avg_cadence = activity_data["avg_cadence"]
            if activity_data.get("notes"):
                activity.notes = activity_data["notes"]
            activity.source = self.provider_name

            # Set additional provider IDs from spreadsheet
            if activity_data.get("strava_id"):
                activity.strava_id = activity_data["strava_id"]
            if activity_data.get("garmin_id"):
                activity.garmin_id = activity_data["garmin_id"]
            if activity_data.get("ridewithgps_id"):
                activity.ridewithgps_id = activity_data["ridewithgps_id"]

            # Store the raw provider data
            activity.spreadsheet_data = json.dumps(activity_data)

            # Save the activity
            activity.save()
            persisted_activities.append(activity)

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)

        return persisted_activities

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

    def fetch_activities(self) -> List[Activity]:
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        if sheet is None:
            return []

        activities: List[Activity] = []
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                continue  # Skip header row
            activity_kwargs: Dict[str, Any] = {}
            # Convert date to GMT timestamp
            departed_at = self._convert_to_gmt_timestamp(row[0])
            activity_kwargs["departed_at"] = departed_at

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
                activity_kwargs["duration"] = self._hms_to_seconds(row[7])
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
            activities.append(Activity(**activity_kwargs))
        return activities

    def fetch_activities_for_month(self, year_month: str) -> List[Activity]:
        """
        Return activities for the given year_month (YYYY-MM).
        """
        all_activities = self.fetch_activities()
        filtered = []
        for act in all_activities:
            departed_at = getattr(act, "departed_at", None)
            if departed_at:
                try:
                    # Convert GMT timestamp to local time for comparison
                    dt = datetime.datetime.fromtimestamp(int(departed_at))
                    date_str = dt.strftime("%Y-%m")
                    if date_str == year_month:
                        filtered.append(act)
                except (ValueError, TypeError):
                    continue
        return filtered

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        xlsx_file = Path(self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        row_idx = int(activity_id)
        if row_idx <= 1 or row_idx > sheet.max_row:
            return None

        row = [cell.value for cell in sheet[row_idx]]
        activity_kwargs: Dict[str, Any] = {}
        departed_at = self._convert_to_gmt_timestamp(row[0]) if row[0] else None
        activity_kwargs["departed_at"] = departed_at
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
            activity_kwargs["duration"] = self._hms_to_seconds(row[7])
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
        return Activity(**activity_kwargs)

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        xlsx_file = Path("ActivityData", self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        row_idx = int(activity_id)
        if row_idx <= 1 or row_idx > sheet.max_row:
            return False

        # Prepare the row in the same order as the header
        row = [
            getattr(activity, "start_time", ""),
            getattr(activity, "activity_type", ""),
            getattr(activity, "location_name", ""),
            getattr(activity, "city", ""),
            getattr(activity, "state", ""),
            getattr(activity, "temperature", ""),
            getattr(activity, "equipment", ""),
            self._seconds_to_hms(getattr(activity, "duration", None)),
            getattr(activity, "distance", ""),
            getattr(activity, "max_speed", ""),
            getattr(activity, "avg_heart_rate", ""),
            getattr(activity, "max_heart_rate", ""),
            getattr(activity, "calories", ""),
            getattr(activity, "max_elevation", ""),
            getattr(activity, "total_elevation_gain", ""),
            getattr(activity, "with_names", ""),
            getattr(activity, "avg_cadence", ""),
            getattr(activity, "strava_id", ""),
            getattr(activity, "garmin_id", ""),
            getattr(activity, "ridewithgps_id", ""),
            getattr(activity, "notes", ""),
        ]
        for col_idx, value in enumerate(row, start=1):
            sheet.cell(row=row_idx, column=col_idx, value=value)
        wb_obj.save(xlsx_file)
        return True

    def get_gear(self) -> Dict[str, str]:
        xlsx_file = Path("ActivityData", self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        gear_set = set()
        # The equipment column is index 6 (0-based)
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                continue  # Skip header row
            equipment = row[6]
            if equipment:
                gear_set.add(str(equipment))
        # Use the equipment name as both key and value
        return {name: name for name in gear_set}

    def create_activity(self, activity: Activity) -> str:
        xlsx_file = Path("ActivityData", self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        row = [
            getattr(activity, "start_time", ""),
            getattr(activity, "activity_type", ""),
            getattr(activity, "location_name", ""),
            getattr(activity, "city", ""),
            getattr(activity, "state", ""),
            getattr(activity, "temperature", ""),
            getattr(activity, "equipment", ""),
            self._seconds_to_hms(getattr(activity, "duration", None)),
            getattr(activity, "distance", ""),
            getattr(activity, "max_speed", ""),
            getattr(activity, "avg_heart_rate", ""),
            getattr(activity, "max_heart_rate", ""),
            getattr(activity, "calories", ""),
            getattr(activity, "max_elevation", ""),
            getattr(activity, "total_elevation_gain", ""),
            getattr(activity, "with_names", ""),
            getattr(activity, "avg_cadence", ""),
            getattr(activity, "strava_id", ""),
            getattr(activity, "garmin_id", ""),
            getattr(activity, "ridewithgps_id", ""),
            getattr(activity, "notes", ""),
        ]
        sheet.append(row)
        wb_obj.save(xlsx_file)
        return str(sheet.max_row)

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        xlsx_file = Path("ActivityData", self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        row_idx = int(activity_id)
        # The gear column is index 7 (0-based), so column 7+1=8 (1-based for openpyxl)
        gear_col = 7 + 1
        if row_idx <= 1 or row_idx > sheet.max_row:
            return False  # Invalid row (header or out of range)
        sheet.cell(row=row_idx, column=gear_col, value=gear_id)
        wb_obj.save(xlsx_file)
        return True
