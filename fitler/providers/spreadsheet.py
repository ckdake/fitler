"""Local provider for activities stored in a spreadsheet."""
from typing import List, Dict, Any, Optional
from pathlib import Path
import openpyxl
from dateutil import parser as dateparser

from fitler.providers.base import FitnessProvider, Activity

class SpreadsheetActivities(FitnessProvider):
    def __init__(self, path: str):
        self.path = path

    def fetch_activities(self) -> List[Activity]:
        xlsx_file = Path("ActivityData", self.path)
        wb_obj = openpyxl.load_workbook(xlsx_file)
        sheet = wb_obj.active

        activities: List[Activity] = []
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                continue  # Skip header row
            activity_kwargs: Dict[str, Any] = {}
            activity_kwargs["start_time"] = dateparser.parse(str(row[0])).strftime("%Y-%m-%d")
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
                activity_kwargs["duration_hms"] = row[7]
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
            provider_ids = {}
            if row[17]:
                provider_ids["strava"] = row[17]
            if row[18]:
                provider_ids["garmin"] = row[18]
            if row[19]:
                provider_ids["ridewithgps"] = row[19]
            if row[20]:
                activity_kwargs["notes"] = row[20]
            activity_kwargs["provider_ids"] = provider_ids
            activity_kwargs["source_file"] = str(xlsx_file)
            activity_kwargs["source_file_type"] = "spreadsheet"
            activities.append(Activity(**activity_kwargs))
        return activities

    def upload_activity(self, activity: Activity) -> str:
        raise NotImplementedError("LocalSpreadsheetProvider does not support uploading activities.")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        raise NotImplementedError("LocalSpreadsheetProvider does not support fetching by ID.")

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        raise NotImplementedError("LocalSpreadsheetProvider does not support updating activities.")

    def get_gear(self) -> Dict[str, str]:
        return {}