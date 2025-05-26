import os
import tempfile
import shutil
from fitler.datafiles import ActivityFile, ActivityFileCollection


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


def test_activity_file_parses_gpx(tmp_path):
    gpx_file = create_sample_gpx_file(tmp_path)
    af = ActivityFile(gpx_file)
    metadata = af.parse()
    assert metadata is not None
    assert metadata.start_time.startswith("2024-05-27T")
    assert metadata.source == "File"


def test_activity_file_collection(tmp_path):
    # Create multiple sample files
    gpx1 = create_sample_gpx_file(tmp_path)
    gpx2 = create_sample_gpx_file(tmp_path)
    shutil.copy(gpx1, os.path.join(tmp_path, "test2.gpx"))
    collection = ActivityFileCollection(os.path.join(tmp_path, "*.gpx"))
    collection.process()
    assert len(collection.activities_metadata) >= 2
    for am in collection.activities_metadata:
        assert am.source == "File"
