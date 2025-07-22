"""Defines interactions with files on disk"""

import glob
import tempfile
import gzip
import json

from fitler.activity import Activity
from fitler.fileformats.gpx import parse_gpx
from fitler.fileformats.tcx import parse_tcx
from fitler.fileformats.fit import parse_fit


class ActivityFileCollection(object):
    def __init__(self, folder):
        self.folder = folder
        self.activities_metadata = []

    def process(self, limit=-1):
        gen = glob.iglob(self.folder)

        counter = 0
        for file in gen:
            if limit > 0 and counter == limit:
                break
            else:
                counter += 1
                af = ActivityFile(file)
                am = af.parse()
                self.activities_metadata.append(am)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class ActivityFile(object):
    def __init__(self, file):
        self.file = file
        self.activity_metadata, created = Activity.get_or_create(
            original_filename=file.split("/")[-1]
        )

        if ".fit.gz" in self.file:
            self.file_type = "FIT"
            self.gzipped = 1
        elif ".tcx.gz" in self.file:
            self.file_type = "TCX"
            self.gzipped = 1
        elif ".gpx.gz" in self.file:
            self.file_type = "GPX"
            self.gzipped = 1
        elif ".gpx" in self.file:
            self.file_type = "GPX"
            self.gzipped = 0
        elif ".tcx" in self.file:
            self.file_type = "TCX"
            self.gzipped = 0
        elif ".fit" in self.file:
            self.file_type = "FIT"
            self.gzipped = 0
        else:
            raise ValueError("Why hello there unknown file format!", self.file)

        self.activity_metadata.save()

    def parse(self):
        read_file = self.file
        fp = None

        if self.gzipped:
            fp = tempfile.NamedTemporaryFile()
            with gzip.open(self.file, "rb") as f:
                fp.write(f.read().lstrip())
            read_file = fp.name

        try:
            if "FIT" == self.file_type:
                result = parse_fit(read_file)
            elif "TCX" == self.file_type:
                result = parse_tcx(read_file)
            elif "GPX" == self.file_type:
                result = parse_gpx(read_file)
            else:
                raise ValueError("Why hello there unknown file format!", self.file_type)

            if result.get("start_time"):
                self.activity_metadata.set_start_time(result["start_time"])
            if result.get("distance") is not None:
                self.activity_metadata.distance = result["distance"]
        except Exception as e:
            self.activity_metadata.error = str(e)

        if self.gzipped and fp:
            fp.close()

        self.activity_metadata.source = "File"
        self.activity_metadata.save()
        return self.activity_metadata
