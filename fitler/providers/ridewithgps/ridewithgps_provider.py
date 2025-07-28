"""RideWithGPS provider for Fitler.

This module defines the RideWithGPSProvider class, which provides an interface
for interacting with RideWithGPS activity data, including fetching, creating,
updating activities, and managing gear.
"""

import os
import json
from typing import List, Optional, Dict, Any
from pyrwgps import RideWithGPS
import datetime

from fitler.providers.base_provider import FitnessProvider
from fitler.provider_sync import ProviderSync
from fitler.providers.ridewithgps.ridewithgps_activity import RideWithGPSActivity


class RideWithGPSProvider(FitnessProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.username = os.environ["RIDEWITHGPS_EMAIL"]
        self.password = os.environ["RIDEWITHGPS_PASSWORD"]
        self.apikey = os.environ["RIDEWITHGPS_KEY"]

        self.client = RideWithGPS(apikey=self.apikey, cache=True)

        user_info = self.client.authenticate(self.username, self.password)
        self.userid = getattr(user_info, "id", None)

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "ridewithgps"

    def pull_activities(self, date_filter: Optional[str] = None) -> List[RideWithGPSActivity]:
        """
        Sync activities for a given month filter in YYYY-MM format.
        If date_filter is None, pulls all activities (not implemented yet).
        Returns a list of synced Activity objects that have been persisted to the database.
        """
        # For now, require date_filter
        if date_filter is None:
            print("RideWithGPS provider: pulling all activities not implemented yet")
            return []
        
        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if existing_sync:
            print(f"Month {date_filter} already synced for {self.provider_name}")
            return []

        # Get the raw activity data for the month
        raw_activities = self.fetch_activities_for_month(date_filter)
        print(f"Found {len(raw_activities)} RideWithGPS activities for {date_filter}")

        persisted_activities = []

        for raw_activity in raw_activities:
            try:
                # Create RideWithGPSActivity from raw data
                rwgps_activity = RideWithGPSActivity()
                
                # Set basic activity data (raw_activity is a dict from API)
                rwgps_activity.ridewithgps_id = str(raw_activity.get("id", ""))
                rwgps_activity.name = str(raw_activity.get("name", ""))
                rwgps_activity.activity_type = str(raw_activity.get("type", ""))
                
                # Distance conversion from raw data
                if raw_activity.get("distance"):
                    # RideWithGPS provides distance, need to check units
                    from decimal import Decimal
                    rwgps_activity.distance = Decimal(str(raw_activity.get("distance", 0)))
                
                # Start time
                rwgps_activity.start_time = raw_activity.get("departed_at", "")
                
                # Location data
                if raw_activity.get("locality"):
                    rwgps_activity.city = str(raw_activity.get("locality", ""))
                if raw_activity.get("administrative_area"):
                    rwgps_activity.state = str(raw_activity.get("administrative_area", ""))
                
                # Store raw data as JSON
                rwgps_activity.raw_data = json.dumps(raw_activity)
                
                # Check for duplicates based on ridewithgps_id
                existing = RideWithGPSActivity.get_or_none(
                    RideWithGPSActivity.ridewithgps_id == str(raw_activity.get("id", ""))
                )
                if existing:
                    print(f"Skipping duplicate RideWithGPS activity {raw_activity.get('id')}")
                    continue
                
                # Save to ridewithgps_activities table
                rwgps_activity.save()
                persisted_activities.append(rwgps_activity)
                
            except Exception as e:
                print(f"Error processing RideWithGPS activity: {e}")
                continue

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)
        
        print(f"Synced {len(persisted_activities)} RideWithGPS activities to ridewithgps_activities table")
        return persisted_activities

    # Abstract method implementations
    def create_activity(self, activity_data: Dict) -> RideWithGPSActivity:
        """Create a new RideWithGPSActivity from activity data."""
        # Create new activity
        return RideWithGPSActivity.create(**activity_data)

    def get_activity_by_id(self, activity_id: str) -> Optional[RideWithGPSActivity]:
        """Get a RideWithGPSActivity by its provider ID."""
        return RideWithGPSActivity.get_or_none(RideWithGPSActivity.ridewithgps_id == activity_id)

    def update_activity(self, activity_data: Dict) -> RideWithGPSActivity:
        """Update an existing RideWithGPSActivity with new data."""
        provider_id = activity_data['ridewithgps_id']
        activity = RideWithGPSActivity.get(RideWithGPSActivity.ridewithgps_id == provider_id)
        for key, value in activity_data.items():
            setattr(activity, key, value)
        activity.save()
        return activity

    def get_gear(self) -> Dict[str, str]:
        """Get gear from RideWithGPS - return empty dict for now."""
        # TODO: Implement gear fetching from RideWithGPS API
        return {}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        raise NotImplementedError("Setting gear on RideWithGPS not implemented")

    def fetch_activities_for_month(self, year_month: str) -> List[Dict]:
        """
        Return activities for the given year_month (YYYY-MM).
        """
        all_activities = self.fetch_activities()
        filtered = []
        year, month = map(int, year_month.split("-"))
        for act in all_activities:
            start_time = getattr(act, "start_time", None)
            if start_time:
                try:
                    # Convert GMT timestamp to local time for filtering
                    dt = datetime.datetime.fromtimestamp(int(start_time))
                    if dt.year == year and dt.month == month:
                        # Convert activity object to dict for processing
                        activity_dict = {
                            "id": getattr(act, "ridewithgps_id", None),
                            "name": getattr(act, "name", None),
                            "distance": getattr(act, "distance", None),
                            "departed_at": start_time,
                            "locality": None,  # Not available in basic fetch
                            "administrative_area": None,  # Not available in basic fetch
                        }
                        filtered.append(activity_dict)
                except (ValueError, TypeError):
                    continue
        return filtered

    def fetch_activities(self) -> List[RideWithGPSActivity]:
        """Fetch all activities from RideWithGPS and return as RideWithGPSActivity objects."""
        activities = []
        try:
            trips = self.client.list(f"/users/{self.userid}/trips.json")
            gear = self.get_gear()
            for trip in trips:
                try:
                    departed_at = getattr(trip, "departed_at", None)
                    dt = self._parse_ridewithgps_datetime(departed_at)
                    if dt:
                        # Convert to UTC and get timestamp
                        utc_dt = dt.astimezone(datetime.timezone.utc)
                        timestamp = int(utc_dt.timestamp())
                    else:
                        timestamp = None
                    gear_id = getattr(trip, "gear_id", None)
                    gear_id_str = str(gear_id) if gear_id is not None else None
                    
                    # Create RideWithGPSActivity object
                    rwgps_activity = RideWithGPSActivity()
                    rwgps_activity.start_time = timestamp
                    rwgps_activity.distance = getattr(trip, "distance", 0) * 0.00062137  # meters to miles
                    rwgps_activity.ridewithgps_id = str(getattr(trip, "id", ""))
                    rwgps_activity.name = str(getattr(trip, "name", ""))
                    rwgps_activity.equipment = gear.get(gear_id_str, "") if gear_id_str else ""
                    # Convert trip object to serializable dict
                    try:
                        if hasattr(trip, '__dict__'):
                            trip_dict = {}
                            for key, value in trip.__dict__.items():
                                try:
                                    # Test if value is JSON serializable
                                    json.dumps(value)
                                    trip_dict[key] = value
                                except (TypeError, ValueError):
                                    # Convert non-serializable objects to string
                                    trip_dict[key] = str(value)
                            rwgps_activity.raw_data = json.dumps(trip_dict)
                        else:
                            rwgps_activity.raw_data = json.dumps({})
                    except Exception:
                        rwgps_activity.raw_data = json.dumps({})
                    
                    activities.append(rwgps_activity)
                except Exception as e:
                    print("Exception fetching RideWithGPS Activity:", e)
        except Exception as e:
            print(f"Error fetching RideWithGPS activities: {e}")
        return activities

    def _parse_ridewithgps_datetime(self, dt_val):
        """Parse RideWithGPS datetime strings."""
        from dateutil import parser as dt_parser

        if not dt_val:
            return None
        try:
            # Parse the ISO8601 string which includes timezone
            dt = dt_parser.parse(str(dt_val))
            # At this point dt should have the correct timezone (-05:00)
            if dt and dt.tzinfo is None:
                # If somehow we get a naive datetime, assume local
                dt = dt.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
            # Keep the parsed datetime in its original timezone
            return dt
        except Exception:
            return None
