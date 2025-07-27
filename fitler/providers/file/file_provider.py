"""File provider for Fitler.

This module defines the FileProvider class, which provides an interface
for processing activity files from the filesystem (GPX, FIT, TCX, etc).
"""

import os
import glob
import hashlib
import json
import tempfile
import gzip
from pathlib import Path
from typing import List, Optional
from fitler.providers.base_provider import FitnessProvider
from fitler.activity import Activity
from fitler.provider_sync import ProviderSync
from fitler.providers.file.file_activity import FileActivity
from peewee import DoesNotExist


class FileProvider(FitnessProvider):
    """File provider for processing activity files from filesystem."""

    def __init__(self, file_glob: str):
        """Initialize with file glob pattern for finding activity files."""
        self.file_glob = file_glob

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "file"

    def pull_activities(self, date_filter: Optional[str] = None) -> List[Activity]:
        """
        Process activity files matching the glob pattern.
        If date_filter is provided (YYYY-MM format), only returns activities from that month.
        If date_filter is None, processes all files.
        Returns an empty list for now since we're only populating provider tables.
        """
        # If no date filter, process all files without sync checking
        if date_filter is None:
            return self._pull_all_activities()

        # Check if this month has already been synced for this provider
        existing_sync = ProviderSync.get_or_none(date_filter, self.provider_name)
        if existing_sync:
            print(f"Month {date_filter} already synced for {self.provider_name}")
            return []

        # Find all files matching the glob pattern
        file_paths = glob.glob(self.file_glob)
        print(f"Found {len(file_paths)} files matching pattern: {self.file_glob}")

        processed_count = 0

        for file_path in file_paths:
            try:
                self._process_file(file_path, date_filter)
                processed_count += 1
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

        print(f"Processed {processed_count} files into file_activities table")

        # Mark this month as synced
        ProviderSync.create(year_month=date_filter, provider=self.provider_name)

        return []

    def _pull_all_activities(self) -> List[Activity]:
        """Process all files matching the glob pattern without date filtering."""
        # Find all files matching the glob pattern
        file_paths = glob.glob(self.file_glob)
        print(f"Found {len(file_paths)} files matching pattern: {self.file_glob}")

        processed_count = 0

        for file_path in file_paths:
            try:
                # Process file without date filter (pass None to skip date checks)
                self._process_file(file_path, None)
                processed_count += 1
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

        print(f"Processed {processed_count} files into file_activities table")
        return []

    def _process_file(
        self, file_path: str, date_filter: Optional[str]
    ) -> None:
        """Process a single activity file and store in file_activities table."""
        # Calculate file checksum
        checksum = self._calculate_checksum(file_path)
        file_size = str(os.path.getsize(file_path))

        # Determine file format and if it's gzipped
        file_format, is_gzipped = self._determine_file_format(file_path)

        # Check if we've already processed this exact file
        try:
            existing_file_activity = FileActivity.get(
                FileActivity.file_path == file_path,
                FileActivity.file_checksum == checksum,
            )
            # File already processed, skip
            return

        except DoesNotExist:
            pass  # File not processed yet, continue

        # Parse the file based on format
        parsed_data = self._parse_file(file_path, file_format, is_gzipped)
        if not parsed_data:
            return

        # Check if this activity should be included based on date filter (skip if no filter)
        if date_filter is not None and not self._parsed_data_matches_date_filter(
            parsed_data, date_filter
        ):
            return

        # Create FileActivity record
        file_activity = FileActivity.create(
            file_path=file_path,
            file_checksum=checksum,
            file_size=file_size,
            file_format=file_format,
            name=parsed_data.get("name", ""),
            distance=parsed_data.get("distance", 0),
            start_time=parsed_data.get("start_time", ""),
            activity_type=parsed_data.get("activity_type", ""),
            duration_hms=parsed_data.get("duration_hms", ""),
            raw_data=json.dumps(parsed_data),
        )

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

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _activity_matches_date_filter(
        self, activity: Activity, date_filter: str
    ) -> bool:
        """Check if an activity matches the date filter (YYYY-MM)."""
        if not activity.date:
            return False

        year, month = map(int, date_filter.split("-"))
        return activity.date.year == year and activity.date.month == month

    def _parsed_data_matches_date_filter(
        self, parsed_data: dict, date_filter: str
    ) -> bool:
        """Check if parsed data matches the date filter."""
        start_time = parsed_data.get("start_time")
        if not start_time:
            return False

        try:
            from datetime import datetime

            if isinstance(start_time, str):
                # Try to parse as Unix timestamp
                try:
                    dt = datetime.fromtimestamp(int(start_time))
                except ValueError:
                    # Try to parse as ISO string
                    import dateparser

                    dt = dateparser.parse(start_time)
            else:
                dt = start_time

            if dt:
                year, month = map(int, date_filter.split("-"))
                return dt.year == year and dt.month == month
        except Exception:
            pass

        return False

    # Required abstract methods (not implemented for files)
    def create_activity(self, activity: Activity) -> str:
        raise NotImplementedError("File provider does not support creating activities")

    def get_activity_by_id(self, activity_id: str) -> Optional[Activity]:
        """Get activity by file path."""
        try:
            file_activity = FileActivity.get(FileActivity.file_path == activity_id)
            logical_activity = (
                Activity.select()
                .where(
                    Activity.source == "file",
                    Activity.original_filename
                    == os.path.basename(file_activity.file_path),
                )
                .first()
            )
            return logical_activity
        except DoesNotExist:
            return None

    def update_activity(self, activity_id: str, activity: Activity) -> bool:
        raise NotImplementedError("File provider does not support updating activities")

    def get_gear(self) -> dict:
        return {}

    def set_gear(self, gear_id: str, activity_id: str) -> bool:
        return False
