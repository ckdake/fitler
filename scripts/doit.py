import fitler
import os
import copy

# Fire up the db
fitler.ActivityMetadata.migrate()


###### Load the spreadsheet in as 'Spreadsheet'
# spreadsheet = fitler.ActivitySpreadsheet('/Users/ckdake/Documents/exerciselog.xlsx')
# spreadsheet.parse()
# print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

###### Load the files in as 'File'
# activityfiles = fitler.ActivityFileCollection('./export*/activities/*')
# activityfiles.process()  #can limit here to 10
# print("Files parsed: ", len(activityfiles.activities_metadata))

###### Load from Strava as 'Strava'
# stravabits = fitler.StravaActivities(os.environ['STRAVA_ACCESS_TOKEN'])
# stravabits.process()
# print("Strava Activities pulled from API: ", len(stravabits.activities_metadata))

###### Load from our strava local files as 'StravaFile'
# stravabits = fitler.StravaJsonActivities('/Users/ckdake/.stravadata/activities_5850/*')
# stravabits.process()
# print("Strava Activities pulled from files: ", len(stravabits.activities_metadata))

###### Load from RidewithGPS as 'RidewithGPS'
# ridewithgpsbits = fitler.RideWithGPSActivities(os.environ['RIDWITHGPS_ACCSS_TOKEN'])
# ridewithgpsbits.process()
# print("RideWithGPS Activities pulled: ", len(ridewithgpsbits.activiteis_metadata))

###### Load from Garmin somehow.


# Populate the "Main" from the spreadsheet if we need to
if fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main").count() == 0:
    for activity in fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Spreadsheet"):
        activity_copy = copy.deepcopy(activity)
        activity_copy.id = None
        activity_copy.source = 'Main'
        activity_copy.save()

# Fill in the missing file IDs from File using ~match.  How many are missing?
missingfiles = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.original_filename == None)
print('--------- Main is missing file for:', len(missingfiles), '---------')

# Fill in the missing strava IDs from Strava using ~match. How many are missing?
missingstrava = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == None)
print('--------- Main is missing strava_id for:', len(missingstrava), '---------')

# Fill in the missing garmin IDs from Garmin using ~match. How many are missing?
missinggarmin = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.garmin_id == None)
print('--------- Main is missing garmin_id for:', len(missinggarmin), '---------')

# Fill in the missing RidewithGPS IDs from RidewithGPS using ~match. How many are missing?
missingridebygps = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.ridewithgps_id == None)
print('--------- Main is missing ridewithgps_id for:', len(missingridebygps), '---------')





exit()



nomatches = []
toomanymatches = []
missingdistance = []

# iterate through the files
for fam in spreadsheet.activities_metadata:
    print('-----------')
    print("Matching:", fam.date, '-', fam.distance, '-', fam.original_filename)
    if (fam.distance):
        matches = 0
        for am in fitler.ActivityMetadata.select().where(
                fitler.ActivityMetadata.date == fam.date,
                fitler.ActivityMetadata.distance <= fam.distance * 1.2,
                fitler.ActivityMetadata.distance >= fam.distance * 0.8
            ):
            matches += 1
            # TODO: this is the merge! may not be right.
            am.original_filename = fam.original_filename
            am.save()
            print("~", am.date, "-", am.distance, "-", am.original_filename)
        for am in fitler.ActivityMetadata.select().where(
                fitler.ActivityMetadata.date == fam.date,
                fitler.ActivityMetadata.distance > fam.distance * 1.2
            ):
            print("+", am.date, "-", am.distance, "-", am.original_filename)
        for am in fitler.ActivityMetadata.select().where(
                fitler.ActivityMetadata.date == fam.date,
                fitler.ActivityMetadata.distance < fam.distance * 0.8
            ):
            print("-", am.date, "-", am.distance, "-", am.original_filename)
        if (matches < 2):
            print("Error: no matches!")
            nomatches.append(fam)
        elif (matches > 2):
            print("Error: too many matches!")
            toomanymatches.append(fam)
    else:
        print("Error: missing distance")
        missingdistance.append(fam)

print('--------------------------------------------------')
activites = fitler.ActivityMetadata.select()
print('--------- TOTAL:', len(activites), '--------------')
print('--------- NO MATCHES:', len(nomatches), '---------')
# for am in nomatches:
#     print(am.original_filename)

print('--------- TOO MANY MATCHES:', len(toomanymatches), '---------')
# for am in toomanymatches:
#     print(am.original_filename)

print('--------- MISSING DISTANCE:', len(missingdistance), '---------')
# for am in missingdistance:
#     print(am.original_filename)
