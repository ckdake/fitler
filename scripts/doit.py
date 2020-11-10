import fitler
import os

###### Fire up the db
fitler.ActivityMetadata.migrate()

###### load up all the activites from the spreadsheet into metadata format
spreadsheet = fitler.ActivitySpreadsheet('/Users/ckdake/Documents/exerciselog.xlsx')
spreadsheet.parse()
print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

###### load up all the activities from the files into metadata format
# activityfiles = fitler.ActivityFileCollection('./export*/activities/*')
# activityfiles.process()  #can limit here to 10
# print("Files parsed: ", len(activityfiles.activities_metadata))

###### slurp a little in from strava
# stravabits = fitler.StravaActivities(os.environ['STRAVA_ACCESS_TOKEN'])
# stravabits.process()
# print("Strava Activities pulled from API: ", len(stravabits.activities_metadata))
### Just load from our local files instead!
stravabits = fitler.StravaJsonActivities('/Users/ckdake/.stravadata/activities_5850/*')
stravabits.process()
print("Strava Activities pulled from files: ", len(stravabits.activities_metadata))

###### and some ridewithgps
# ridewithgpsbits = fitler.RideWithGPSActivities(os.environ['RIDWITHGPS_ACCSS_TOKEN'])
# ridewithgpsbits.process()
# print("RideWithGPS Activities pulled: ", len(ridewithgpsbits.activiteis_metadata))


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

# now, iterate through the spreadsheet, who is missing files?
missingfiles = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.original_filename == None)
print('--------- MISSING FILE:', len(missingfiles), '---------')

missinggarmin = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.garmin_id == None)
print('--------- MISSING Garmin:', len(missinggarmin), '---------')

missingstrava = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.strava_id == None)
print('--------- MISSING Strava:', len(missingstrava), '---------')

missingridebygps = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.ridewithgps_id == None)
print('--------- MISSING RidewithGPS:', len(missingridebygps), '---------')