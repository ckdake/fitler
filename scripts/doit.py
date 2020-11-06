import fitler

# Fire up the db
fitler.ActivityMetadata.migrate()

# load up all the activites from the spreadsheet into metadata format
spreadsheet = fitler.ActivitySpreadsheet('/Users/ckdake/Documents/exerciselog.xlsx')
spreadsheet.parse()
print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

# load up all the activities from the files into metadata format
activityfiles = fitler.ActivityFileCollection('./export*/activities/*')
activityfiles.process(20)  #can limit here to 10
print("Files parsed: ", len(activityfiles.activities_metadata))

nomatches = []
toomanymatches = []
missingdistance = []

# iterate through the files
for fam in activityfiles.activities_metadata:
    print('-----------')
    print("Matching:", fam.original_filename)
    if (fam.distance):
        matches = 0
        for am in fitler.ActivityMetadata.select().where(
                fitler.ActivityMetadata.date == fam.date,
                fitler.ActivityMetadata.distance <= fam.distance * 1.1,
                fitler.ActivityMetadata.distance >= fam.distance * 0.9
            ):
            matches += 1
            # TODO: this is the merge! may not be right.
            am.original_filename = fam.original_filename
            am.save()
            print("~", am.date, "-", am.distance, "-", am.original_filename)
        for am in fitler.ActivityMetadata.select().where(
                fitler.ActivityMetadata.date == fam.date,
                fitler.ActivityMetadata.distance > fam.distance * 1.1
            ):
            print("+", am.date, "-", am.distance, "-", am.original_filename)
        for am in fitler.ActivityMetadata.select().where(
                fitler.ActivityMetadata.date == fam.date,
                fitler.ActivityMetadata.distance < fam.distance * 0.9
            ):
            print("-", am.date, "-", am.distance, "-", am.original_filename)
        if (matches < 2):
            print("Error: no matches!")
            nomatches.append(am)
        elif (matches > 2):
            print("Error: too many matches!")
            toomanymatches.append(am)
    else:
        print("Error: missing distance")
        missingdistance.append(am)

print('--------------------------------------------------')
print('--------- NO MATCHES:', len(nomatches), '---------')
for am in nomatches:
    print(am.original_filename)

print('--------- TOO MANY MATCHES:', len(toomanymatches), '---------')
for am in toomanymatches:
    print(am.original_filename)

print('--------- MISSING DISTANCE:', len(missingdistance), '---------')
for am in missingdistance:
    print(am.original_filename)

# now, iterate through the spreadsheet, who is missing files?
missingfiles = fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.original_filename == None)
print('--------- MISSING FILE:', len(missingfiles), '---------')