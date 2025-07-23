import os
import tempfile
import shutil
from fitler.providers.file.file_provider import FileProvider


def create_sample_gpx_file(tmpdir):
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="pytest">
  <trk>
    <name>Test GPX</name>
    <trkseg>
      <trkpt lat="38.5" lon="-120.2"><ele>1000</ele><time>2024-05-27T12:00:00Z</time></trkpt>
      <trkpt lat="40.7" lon="-120.95"><ele>2000</ele><time>2024-05-27T12:10:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    gpx_path = os.path.join(tmpdir, "test.gpx")
    with open(gpx_path, "w") as f:
        f.write(gpx_content)
    return gpx_path


def test_file_provider_parses_gpx(tmp_path):
    gpx_file = create_sample_gpx_file(tmp_path)
    provider = FileProvider(gpx_file)
    activities = provider.pull_activities("2024-05")  # Match the date in our test data
    assert len(activities) >= 1
    activity = activities[0]
    # start_time is now stored as Unix timestamp string
    assert str(activity.start_time).isdigit()
    assert activity.source == "file"


def test_file_provider_processes_multiple_files(tmp_path):
    # Create multiple sample files
    gpx1 = create_sample_gpx_file(tmp_path)
    gpx2 = create_sample_gpx_file(tmp_path)
    shutil.copy(gpx1, os.path.join(tmp_path, "test2.gpx"))
    
    # Use FileProvider to process multiple files
    provider = FileProvider(os.path.join(tmp_path, "*.gpx"))
    activities = provider.pull_activities("2024-05")  # Match the date in our test data
    
    assert len(activities) >= 2
    for activity in activities:
        assert activity.source == "file"


def test_activity_file_determines_format():
    """Test file format detection."""
    from fitler.providers.file.file_provider import FileProvider
    
    # Test with a real FileProvider
    provider = FileProvider("*.gpx")
    
    format_type, is_gzipped = provider._determine_file_format("test.gpx")
    assert format_type == "gpx"
    assert is_gzipped is False
    
    format_type, is_gzipped = provider._determine_file_format("test.gpx.gz")
    assert format_type == "gpx"
    assert is_gzipped is True
    
    format_type, is_gzipped = provider._determine_file_format("test.fit")
    assert format_type == "fit"
    assert is_gzipped is False
    
    format_type, is_gzipped = provider._determine_file_format("test.fit.gz")
    assert format_type == "fit"
    assert is_gzipped is True


def test_file_provider_handles_gzipped(tmp_path):
    """Test that gzipped files are properly handled."""
    import gzip
    
    # Create a gzipped GPX file
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="pytest">
  <trk>
    <name>Test Gzipped GPX</name>
    <trkseg>
      <trkpt lat="38.5" lon="-120.2"><ele>1000</ele><time>2024-05-27T12:00:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>
"""
    
    gpx_gz_path = os.path.join(tmp_path, "test.gpx.gz")
    with gzip.open(gpx_gz_path, "wt") as f:
        f.write(gpx_content)
    
    provider = FileProvider(gpx_gz_path)
    
    # Test format detection
    format_type, is_gzipped = provider._determine_file_format(gpx_gz_path)
    assert format_type == "gpx"
    assert is_gzipped == True
    
    # Test parsing
    activities = provider.pull_activities("2024-05")
    assert len(activities) >= 1
    activity = activities[0]
    assert activity.source == "file"


def test_file_provider_initialization():
    """Test FileProvider initialization."""
    provider = FileProvider("/tmp/*.gpx")
    assert provider.file_glob == "/tmp/*.gpx"
    assert provider.provider_name == "file"
