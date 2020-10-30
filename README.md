## Get your data

Ask strava for a dump. Get it! It will contain a bunch of things including
an activities folder with the following filetyles:

.fit.gz
.gpx
.tcx.gz
.gpx.gz

It should be named export_123455 (your user id). Put it in this folder.

## Running

pip3 install virtualenv --user
virtualenv env
source env/bin/activate
pip3 install -r requirements.txt
python3 fitler.py
deactivate


## TODO

Get everything out of gpx files: https://pypi.org/project/gpxpy/
Get everything out of tcx files: https://pypi.org/project/python-tcxparser/
Get everything out of fit files: https://github.com/dtcooper/python-fitparse/ 

Get everything out of a spreadsheet with headers
Correlate spreadsheet entries with files into object representation

Generate JSON blob that represents all the metadata and let people use it.

Output as all fit
Output as all tcx
Output as all gpx
Output as all kml
Output as all geojson

Correlate each entry with Strava API
Correlate each entry with RidewithGPS API

Can we get whoop scores for each one?
What is in TrainingPeaks?
What is in Wandrer.earth?
What about the weather?
What about choochoo?
