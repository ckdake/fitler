"""File provider for Fitler.

This module defines the FileProvider class, which provides an interface
for processing activity files from the filesystem (GPX, FIT, TCX, etc).

TODO: get this to follow the patterns of the other provider.
"""

import os
import glob
import hashlib
import json
import datetime
import dateparser
import logging
import tempfile
import gzip
from pathlib import Path
from typing import List, Optional, Dict, Any
from fitler.providers.base_provider import FitnessProvider
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from fitler.providers.file.file_activity import FileActivity
from peewee import DoesNotExist


class FileProvider(FitnessProvider):
    """File provider for processing activity files from filesystem."""

    def __init__(self, file_glob: str, config: Optional[Dict[str, Any]] = None):
        """Initialize with file glob pattern for finding activity files."""
        super().__init__(config)
        self.file_glob = file_glob

        if self.config:
            self.debug = self.config.get("debug", False)
            if self.debug:
                logging.basicConfig(level=logging.DEBUG)

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "file"

    def pull_activities(
        self, date_filter: Optional[str] = None
    ) -> List["FileActivity"]:
        """
        Process activity files and return FileActivity objects.
        If date_filter is provided (YYYY-MM format), only returns activities from that month.
        If date_filter is None, processes all files and returns all FileActivity objects.
        """
        # If no date filter, process all files without sync checking
        if date_filter is None:
            return self._pull_all_activities()

        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if not existing_sync:
            # First time processing this month - process files
            file_paths = glob.glob(self.file_glob)
            print(f"Found {len(file_paths)} files matching pattern: {self.file_glob}")

            processed_count = 0
            for file_path in file_paths:
                try:
                    file_activity = self._process_file(file_path, date_filter)
                    if file_activity:
                        processed_count += 1
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                    continue

            print(f"Processed {processed_count} files into file_activities table")

            # Mark this month as synced
            ProviderSync.create(year_month=date_filter, provider=self.provider_name)
        else:
            print(f"Month {date_filter} already synced for {self.provider_name}")

        # Always return activities for the requested month from database
        return self._get_file_activities_for_month(date_filter)

    def _pull_all_activities(self) -> List["FileActivity"]:
        """Process all files matching the glob pattern without date filtering."""
        # Find all files matching the glob pattern
        file_paths = glob.glob(self.file_glob)
        print(f"Found {len(file_paths)} files matching pattern: {self.file_glob}")

        processed_activities = []
        processed_count = 0

        for file_path in file_paths:
            try:
                # Process file without date filter (pass None to skip date checks)
                file_activity = self._process_file(file_path, None)
                if file_activity:
                    processed_activities.append(file_activity)
                    processed_count += 1
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

        print(f"Processed {processed_count} files into file_activities table")
        # Return all processed activities (no date filtering for this method)
        return processed_activities

    def _get_file_activities_for_month(self, date_filter: str) -> List["FileActivity"]:
        """Get FileActivity objects for a specific month."""
        from fitler.providers.file.file_activity import FileActivity

        year, month = map(int, date_filter.split("-"))
        file_activities = []

        for activity in FileActivity.select():
            if hasattr(activity, "start_time") and activity.start_time:
                try:
                    # Convert timestamp to datetime for comparison
                    dt = datetime.datetime.fromtimestamp(int(activity.start_time))
                    if dt.year == year and dt.month == month:
                        file_activities.append(activity)
                except (ValueError, TypeError):
                    continue

        return file_activities

    def _parse_file(
        self, file_path: str, file_format: str, is_gzipped: bool = False
    ) -> Optional[dict]:
        """Parse an activity file and return activity data."""
        read_file = file_path
        fp = None

        try:
            # Handle gzipped files
            if is_gzipped:
                fp = tempfile.NamedTemporaryFile()
                with gzip.open(file_path, "rb") as f:
                    data = f.read()
                    # For text-based formats (GPX, TCX), strip leading whitespace
                    # For binary formats (FIT), keep the data as-is
                    if file_format in ["gpx", "tcx"]:
                        data = data.lstrip()
                    fp.write(data)
                read_file = fp.name

            # Parse based on format
            if file_format == "gpx":
                from .formats.gpx import parse_gpx

                result = parse_gpx(read_file)
            elif file_format == "fit":
                from .formats.fit import parse_fit

                result = parse_fit(read_file)
            elif file_format == "tcx":
                from .formats.tcx import parse_tcx

                result = parse_tcx(read_file)
            else:
                print(f"Unsupported file format: {file_format}")
                return None

            return result

        except Exception as e:
            print(f"Error parsing {file_format} file {file_path}: {e}")
            return None
        finally:
            # Clean up temporary file
            if fp:
                fp.close()

    def _determine_file_format(self, file_path: str) -> tuple[str, bool]:
        """Determine file format and whether it's gzipped."""
        file_lower = file_path.lower()

        if ".fit.gz" in file_lower:
            return "fit", True
        elif ".tcx.gz" in file_lower:
            return "tcx", True
        elif ".gpx.gz" in file_lower:
            return "gpx", True
        elif file_lower.endswith(".gpx"):
            return "gpx", False
        elif file_lower.endswith(".tcx"):
            return "tcx", False
        elif file_lower.endswith(".fit"):
            return "fit", False
        else:
            raise ValueError(f"Unknown file format: {file_path}")

    def _convert_start_time_to_int(self, start_time_val) -> Optional[int]:
        """Convert various start_time formats to Unix timestamp integer."""
        if not start_time_val:
            return None
        try:
            # If it's already an integer, return it
            if isinstance(start_time_val, int):
                return start_time_val
            # If it's a string that looks like a timestamp
            if isinstance(start_time_val, str) and start_time_val.isdigit():
                return int(start_time_val)
            # Parse as datetime string and convert to timestamp
            dt = dateparser.parse(str(start_time_val))
            if dt:
                return int(dt.timestamp())
        except (ValueError, TypeError, AttributeError):
            pass
        return None

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def get_activity_by_id(self, activity_id: str) -> Optional["FileActivity"]:
        """Get a specific activity by its file activity ID."""
        try:
            from fitler.providers.file.file_activity import FileActivity

            return FileActivity.get_by_id(int(activity_id))
        except (ValueError, DoesNotExist):
            return None

    def update_activity(self, activity_data: Dict[str, Any]) -> Any:
        """File provider does not support updating activities."""
        raise NotImplementedError("File provider does not support updating activities")

    def create_activity(self, activity_data: Dict[str, Any]) -> str:
        """File provider does not support creating activities."""
        raise NotImplementedError("File provider does not support creating activities")

    def get_gear(self) -> Dict[str, str]:
        """Get all unique equipment from file activities."""
        from fitler.providers.file.file_activity import FileActivity

        gear_set = set()
        for activity in FileActivity.select():
            if hasattr(activity, "equipment") and activity.equipment:
                gear_set.add(str(activity.equipment))
        return {name: name for name in gear_set}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        """File provider does not support setting gear."""
        raise NotImplementedError("File provider does not support setting gear")

    def _process_file(
        self, file_path: str, date_filter: Optional[str]
    ) -> Optional["FileActivity"]:
        """Process a single activity file and store in file_activities table."""
        if self.debug:
            print(f"DEBUG: Processing file: {file_path}")

        # Calculate file checksum
        checksum = self._calculate_checksum(file_path)
        file_size = str(os.path.getsize(file_path))
        if self.debug:
            print(f"DEBUG: Checksum: {checksum}, Size: {file_size}")

        # Determine file format and if it is gzipped
        file_format, is_gzipped = self._determine_file_format(file_path)
        if self.debug:
            print(f"DEBUG: Format: {file_format}, Gzipped: {is_gzipped}")

        # Check if we have already processed this exact file
        try:
            existing_file_activity = FileActivity.get(
                FileActivity.file_path == file_path,
                FileActivity.file_checksum == checksum,
            )
            if self.debug:
                print(
                    f"DEBUG: Found existing file activity: {existing_file_activity.id}"
                )
            return existing_file_activity

        except DoesNotExist:
            if self.debug:
                print("DEBUG: File not processed before, continuing")
            pass  # File not processed yet, continue

        # Parse the file based on format
        parsed_data = self._parse_file(file_path, file_format, is_gzipped)
        if not parsed_data:
            if self.debug:
                print("DEBUG: File parsing failed, returning None")
            return None
        if self.debug:
            print(
                f"DEBUG: Parsed data keys: {list(parsed_data.keys()) if parsed_data else None}"
            )

        if self.debug:
            print("DEBUG: Creating FileActivity record...")
        file_activity = FileActivity.create(
            file_path=file_path,
            file_checksum=checksum,
            file_size=file_size,
            file_format=file_format,
            name=parsed_data.get("name", ""),
            distance=parsed_data.get("distance", 0),
            start_time=self._convert_start_time_to_int(parsed_data.get("start_time")),
            activity_type=parsed_data.get("activity_type", ""),
            duration_hms=parsed_data.get("duration_hms", ""),
            raw_data=json.dumps(parsed_data),
        )

        if self.debug:
            print(f"DEBUG: Created FileActivity with ID: {file_activity.id}")
        return file_activity
