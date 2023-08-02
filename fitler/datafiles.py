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
        self.activity_metadata, created = ActivityMetadata.get_or_create(
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
        else:
            raise ValueError("Why hello there unknown file format!", self.file)

        self.activity_metadata.save()

    def parse(self):
        read_file = self.file
        fp = 0

        if self.gzipped:
            fp = tempfile.NamedTemporaryFile()
            with gzip.open(self.file, "rb") as f:
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

        self.activity_metadata.source = "File"
        self.activity_metadata.save()
        return self.activity_metadata

    def process_gpx(self, file):
        # probably should convert these to a TCX file
        # examples at https://github.com/tkrajina/gpxpy/blob/dev/gpxinfo
        gpx_file = open(file, "r")
        gpx = gpxpy.parse(gpx_file)
        self.activity_metadata.set_start_time(str(gpx.get_time_bounds().start_time))
        self.activity_metadata.distance = gpx.length_2d() * 0.00062137

    def process_fit(self, file):
        # should these get converted to tcx, or vice versa?
        # examples at fitdump -n session 998158033.fit
        try:
            fitfile = fitparse.FitFile(file)
            for record in fitfile.get_messages("session"):
                for data in record:
                    if str(data.name) == "start_time":
                        self.activity_metadata.set_start_time(str(data.value))
                    elif data.name == "total_distance":
                        self.activity_metadata.distance = data.value * 0.00062137
        except Exception as e:
            self.activity_metadata.error = str(e)

    def process_tcx(self, file):
        # examples at https://github.com/vkurup/python-tcxparser
        tcx = tcxparser.TCXParser(file)
        self.activity_metadata.set_start_time(str(tcx.started_at))
        self.activity_metadata.distance = tcx.distance * 0.00062137
