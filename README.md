# Fitler

A self contained, non descructive, way to help you understand your activity data.

You'll need a folder of your data files, for now put it in a folder like export_1.

Eventually and optionally you can add in some some api keys or a spreadsheet.

## Use your Strava data if you want

Ask Strava for a dump. Get it! It will contain a bunch of things including
an activities folder with the following filetyles:

.fit.gz
.gpx
.tcx.gz
.gpx.gz

It should be named export_123455 (your user id). Put it in this folder folder.

## Running

    git clone git@github.com:ckdake/fitler.git
    cd fitler
    pip3 install virtualenv --user
    virtualenv env
    source env/bin/activate
    pip3 install -r requirements.txt
    pip3 install .
    python3 scripts/doit.py
    deactivate


## TODO

* Get everything out of gpx files: https://pypi.org/project/gpxpy/
* Get everything out of tcx files: https://pypi.org/project/python-tcxparser/
* Get everything out of fit files: https://github.com/dtcooper/python-fitparse/ 
* Get everythong out of KML files: https://pypi.org/project/pykml/

* Store everything in a SQLite db instead of objects/json: https://github.com/coleifer/peewee


* Get everything out of a spreadsheet with headers: https://pypi.org/project/openpyxl/ 
* Correlate spreadsheet entries with files into object representation


* Generate JSON blob that represents all the metadata and let people use it.


* Output as all fit (lib already included)
* Output as all tcx (lib already included)
* Output as all gpx (lib already included)
* Output as all kml (lib already included)
* Output as all geojson: https://pypi.org/project/geojson/ 


* Correlate each entry with Strava API: https://pypi.org/project/stravaio/ 
* Correlate each entry with RidewithGPS API: Needs an open source python client lib! https://ridewithgps.com/api
* Correlate each entry with Garmin: https://pypi.org/project/garminconnect/ 


* Load files from S3 bucket or somewhere else instead of local: https://pypi.org/project/boto3/ 

* use multiprocessing to spin off workers for individual file parsing, as well as doing each API in parallel: https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing 
* cache things and use shas to know when files have been processed into cache


* Can we get whoop scores for each one?  (via Habitdash export?)
* What is in TrainingPeaks?
* What is in Wandrer.earth?
* What about the weather?
* What about choochoo?
* What else?

## Contributing

PRs that help achieve these goals welcome!  
