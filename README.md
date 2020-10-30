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
...
deactivate

