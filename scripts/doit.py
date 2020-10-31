import fitler


# load up all the activites from the spreadsheet into metadata format
spreadsheet = fitler.ActivitySpreadsheet('/Users/ckdake/Documents/exerciselog.xlsx')
spreadsheet.parse()
print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

# load up all the activities from the files into metadata format
activityfiles = fitler.ActivityFileCollection('./export*/activities/*')
activityfiles.process()  #can limit here to 10
print("Files parsed: ", len(activityfiles.activities_metadata))

# iterate through the files
for fam in activityfiles.activities_metadata:
    # figure out if there is a match in the spreadsheet in a horribly bad way
    matchy = 0
    for sam in spreadsheet.activities_metadata:
        if fam.date == sam.date:
            matchy = 1
            print(
                "Match? (sheet: ", sam.date, "-", sam.activity_type, "-", sam.equipment, "-", sam.strava_id, 
                ") MAY BE: (file", fam.date, "-", fam.original_filename, ")")
    if not matchy:
        print ("NO MATCH: ", fam.original_filename)
