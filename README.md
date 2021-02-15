# Fitler

A self contained, non descructive, way to help you understand your activity data.

You'll need a folder of your data files, for now put it in a folder like data/export_1.

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
    pip3 install -e ./

    mypy fitler/*.py
    black fitler/*.py

    python3 scripts/doit.py
    deactivate


## TODO

    * Write some tests...
    * Build a config object and load it from JSON. Which sources are active and which one is primary, and what "rules" are in place. e.g.:
    ** Spreadsheet is at PATH, and is "primary"
    ** Strava is active, add strava_id to "primary", add "name" from strava to "notes" in primary, add "equipment" from "primary" to RidewithGPS
    ** RidewithGPS is active, add ridewithgps_id to "primary", add "notes" from primary to "name" in RidewithGPS, add "equipment" from "primary" to RidewithGPS

    * Get everything out of gpx files: https://pypi.org/project/gpxpy/  (basics are in, need to fill out metadata, add more fields to db!)
    * Get everything out of tcx files: https://pypi.org/project/python-tcxparser/ (basics are in, need to fill out metadata, add more fields to db!) 
    * Get everything out of fit files: https://github.com/dtcooper/python-fitparse/ (basics are in, need to fill out metadata, add more fields to db!)
    * Get everything out of KML files: https://pypi.org/project/pykml/
    * Get everything out of a spreadsheet with headers: https://pypi.org/project/openpyxl/ (basics are in, work better with headers)

    * Store everything in KM and s per all the filespecs (instead of conversions to mph/miles/etc)
    * Correctly use a datetime with tz information as start time and primary index

    * Output as all fit (lib already included)
    * Output as all tcx (lib already included)
    * Output as all gpx (lib already included)
    * Output as all kml (lib already included)
    * Output as all geojson: https://pypi.org/project/geojson/ 


    * Correlate each entry with Strava API: https://pypi.org/project/stravaio/ (basics of pulling are in, need to figure out pulling all and matching, add more fields to db, what about writing? Updating Name based on authoritative? CK strava has some old janky names)
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
