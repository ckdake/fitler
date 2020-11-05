import fitler

# Fire up the db
fitler.ActivityMetadata.migrate()

# load up all the activites from the spreadsheet into metadata format
spreadsheet = fitler.ActivitySpreadsheet('/Users/ckdake/Documents/exerciselog.xlsx')
spreadsheet.parse()
print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

# load up all the activities from the files into metadata format
activityfiles = fitler.ActivityFileCollection('./export*/activities/*')
activityfiles.process(10)  #can limit here to 10
print("Files parsed: ", len(activityfiles.activities_metadata))

# iterate through the files
for fam in activityfiles.activities_metadata:
    print('-----')
    for am in fitler.ActivityMetadata.select().where(fitler.ActivityMetadata.date == fam.date):
        print(am.date, "-", am.distance, "-", am.original_filename)