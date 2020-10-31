from fitler.metadata import ActivityMetadata

import glob
import tempfile
import gzip
import json

import gpxpy
import gpxpy.gpx
import tcxparser
import fitparse

class ActivityFileCollection(object):
    def __init__(self, folder):
        self.folder = folder 
        self.activities_metadata = []

    def process(self):
        gen = glob.iglob(self.folder)

        for file in gen:
            af = ActivityFile(file)
            am = af.parse()
            self.activities_metadata.append(am)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4) 

class ActivityFile(object):
    def __init__(self, file):
        self.file = file
        self.activity_metadata = ActivityMetadata(file)

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
        else:
            raise ValueError("Why hello there unknown file format!", self.file)

    def parse(self):
        read_file = self.file
        fp = 0

        if self.gzipped:
            fp = tempfile.NamedTemporaryFile()
            with gzip.open(self.file, 'rb') as f:
                fp.write(f.read().lstrip())
            read_file = fp.name

        if "FIT" == self.file_type:
            self.process_fit(read_file)
        elif "TCX" == self.file_type:
            self.process_tcx(read_file)
        elif "GPX" == self.file_type:
            self.process_gpx(read_file)
        else:
            raise ValueError("Why hello there unknown file format!", self.file_type)

        if self.gzipped:
            fp.close()
        return self.activity_metadata

    def process_gpx(self, file):
        gpx_file = open(file, 'r')
        gpx = gpxpy.parse(gpx_file)
        self.activity_metadata.set_start_time(str(gpx.get_time_bounds().start_time))

    def process_fit(self, file):
        try:
            fitfile = fitparse.FitFile(file)
            for record in fitfile.get_messages("record"):
                for data in record:
                    if data.name == "timestamp":
                        self.activity_metadata.set_start_time(str(data.value))
                        break
        except Exception as e:
            self.activity_metadata.error = str(e)
                
    def process_tcx(self, file):
        tcx = tcxparser.TCXParser(file)
        self.activity_metadata.set_start_time(str(tcx.started_at))