import fitler
import os
import copy

##### uncomment this to get SQL Logging
# import logging
# logger = logging.getLogger('peewee')
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)

# Fire up the db
fitler.ActivityMetadata.migrate()

###### Load the spreadsheet in as 'Spreadsheet'
spreadsheet = fitler.ActivitySpreadsheet('~/workspace/fitler/data/exerciselog.xlsx')
spreadsheet.parse()
print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

###### Load the files in as 'File'
# activityfiles = fitler.ActivityFileCollection('~/workspace/fitler/data/export*/activities/*')
# activityfiles.process()  #can limit here to 10
# print("Files parsed: ", len(activityfiles.activities_metadata))

###### Load from Strava as 'Strava'
# stravabits = fitler.StravaActivities(os.environ['STRAVA_ACCESS_TOKEN'])
# stravabits.process()
# print("Strava Activities pulled from API: ", len(stravabits.activities_metadata))

###### Load from our strava local files as 'StravaFile'
stravabits = fitler.StravaJsonActivities('~/.stravadata/activities_5850/*')
stravabits.process()
print("Strava Activities pulled from files: ", len(stravabits.activities_metadata))

###### Load from RidewithGPS as 'RidewithGPS'
# ridewithgpsbits = fitler.RideWithGPSActivities(os.environ['RIDWITHGPS_ACCSS_TOKEN'])
# ridewithgpsbits.process()
# print("RideWithGPS Activities pulled: ", len(ridewithgpsbits.activiteis_metadata))

###### Load from Garmin somehow.

# this is where we match
# targetmetadata is what we want to match on as a dict: {date: '2020-11-07', distance: 1.32 }
# source is where we are looking: "StravaFile"
# return is ActivityMetadata -> the match itself, but only if there is one and only one
def bestmatch(targetmetadata, source):
    # print('-----------')
    # print("Matching:", targetmetadata['date'], '-', targetmetadata['distance'])
    matches = 0
    match = None
    for am in fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == source,
            fitler.ActivityMetadata.date == targetmetadata['date'],
            fitler.ActivityMetadata.distance <= targetmetadata['distance'] * 1.2,
            fitler.ActivityMetadata.distance >= targetmetadata['distance'] * 0.8
        ):
        match = am
        matches += 1
        # print("~", am.date, "-", am.distance)
    for am in fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == source,
            fitler.ActivityMetadata.date == targetmetadata['date'],
            fitler.ActivityMetadata.distance > targetmetadata['distance'] * 1.2
        ):
        matches += 0
        # print("+", am.date, "-", am.distance)
    for am in fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == source,
            fitler.ActivityMetadata.date == targetmetadata['date'],
            fitler.ActivityMetadata.distance < targetmetadata['distance'] * 0.8
        ):
        matches += 0
        # print("-", am.date, "-", am.distance)
    if (matches < 2):
        # print("Error: no matches!")
        return None
    elif (matches > 2):
        # print("Error: too many matches!")
        return None
    return match

# Populate the "Main" from the spreadsheet if we need to
if fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main").count() == 0:
    print("--- Populating Main from Spreadsheet ---")
    for activity in fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Spreadsheet"):
        activity_copy = copy.deepcopy(activity)
        activity_copy.id = None
        activity_copy.source = 'Main'
        activity_copy.save()

# Fill in the missing strava IDs from Strava File using ~match. How many are missing?
missingstrava = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == "")
print('--------- Main is sadly missing strava_id for:', len(missingstrava), '---------')
for activity in missingstrava:
    candidate = bestmatch({'distance': activity.distance, 'date': activity.date}, "StravaFile")
    if candidate:
        print('StravaFile', candidate.strava_id, 'was lonely! Found a match.')
        activity.strava_id = candidate.strava_id
        activity.save()
missingstrava = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == "")
print('--------- Main is now happily only missing strava_id for:', len(missingstrava), '---------')

exit()

# Then do it from actual Strava with ~match. How many are missing?


# Fill in the missing file IDs from File using ~match.  How many are missing?
missingfiles = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.original_filename == None)
print('--------- Main is missing file for:', len(missingfiles), '---------')

# Fill in the missing garmin IDs from Garmin using ~match. How many are missing?
missinggarmin = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.garmin_id == None)
print('--------- Main is missing garmin_id for:', len(missinggarmin), '---------')

# Fill in the missing RidewithGPS IDs from RidewithGPS using ~match. How many are missing?
missingridebygps = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.ridewithgps_id == None)
print('--------- Main is missing ridewithgps_id for:', len(missingridebygps), '---------')
