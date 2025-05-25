import copy

import fitler

def run():
    # uncomment this to get SQL Logging
    # import logging
    # logger = logging.getLogger('peewee')
    # logger.addHandler(logging.StreamHandler())
    # logger.setLevel(logging.DEBUG)

    # Fire up the db
    fitler.ActivityMetadata.migrate()

    # Load the spreadsheet in as 'Spreadsheet'
    spreadsheet = fitler.ActivitySpreadsheet("/home/vscode/exerciselog.xlsx")
    spreadsheet.parse()
    print("Spreadsheet rows parsed: ", len(spreadsheet.activities_metadata))

    # Load the files in as 'File'
    activityfiles = fitler.ActivityFileCollection("./export*/activities/*")
    activityfiles.process()  # can limit here to 10
    print("Files parsed: ", len(activityfiles.activities_metadata))

    # Load from Strava as 'Strava'
    # stravabits = fitler.StravaActivities(os.environ['STRAVA_ACCESS_TOKEN'])
    # stravabits.process()
    # print("Strava Activities pulled from API: ", len(stravabits.activities_metadata))

    # Load from our cached strava local files as 'StravaFile'
    # stravabits = fitler.StravaJsonActivities('/Users/ckdake/.stravadata/activities_5850/*')
    # stravabits.process()
    # print("Strava Activities pulled from files: ", len(stravabits.activities_metadata))

    # Load from RidewithGPS as 'RidewithGPS'
    ridewithgpsbits = fitler.RideWithGPSActivities()
    ridewithgpsbits.process()
    print("RideWithGPS Activities pulled: ", len(ridewithgpsbits.activities_metadata))

    # quit()

    # Load from Garmin somehow.


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
            fitler.ActivityMetadata.date == targetmetadata["date"],
            fitler.ActivityMetadata.distance <= targetmetadata["distance"] * 1.2,
            fitler.ActivityMetadata.distance >= targetmetadata["distance"] * 0.8,
        ):
            match = am
            matches += 1
            # print("~", am.date, "-", am.distance)
        for am in fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == source,
            fitler.ActivityMetadata.date == targetmetadata["date"],
            fitler.ActivityMetadata.distance > targetmetadata["distance"] * 1.2,
        ):
            matches += 0
            # print("+", am.date, "-", am.distance)
        for am in fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == source,
            fitler.ActivityMetadata.date == targetmetadata["date"],
            fitler.ActivityMetadata.distance < targetmetadata["distance"] * 0.8,
        ):
            matches += 0
            # print("-", am.date, "-", am.distance)
        if matches < 1:
            # print("Error: no matches!")
            return None
        elif matches > 1:
            # print("Error: too many matches!")
            return None
        return match


    # Populate the "Main" from the spreadsheet if we need to
    if (
        fitler.ActivityMetadata.select()
        .where(fitler.ActivityMetadata.source == "Main")
        .count()
        == 0
    ):
        print("--- Populating Main from Spreadsheet ---")
        for activity in fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == "Spreadsheet"
        ):
            activity_copy = copy.deepcopy(activity)
            activity_copy.id = None
            activity_copy.source = "Main"
            activity_copy.save()


    # Fill in the missing strava IDs from Strava File using ~match. How many are missing?
    missingstrava = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == ""
    )
    print("--------- Main is sadly missing strava_id for:", len(missingstrava), "---------")
    for activity in missingstrava:
        candidate = bestmatch(
            {"distance": activity.distance, "date": activity.date}, "StravaFile"
        )
        if candidate:
            print("StravaFile", candidate.strava_id, "was lonely! Found a match.")
            activity.strava_id = candidate.strava_id
            activity.save()
    missingstrava = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == ""
    )
    print(
        "--------- Main is now happily only missing strava_id for:",
        len(missingstrava),
        "---------",
    )


    # Then do it from actual Strava with ~match. How many are missing?
    missingstrava = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == ""
    )
    print("--------- Main is sadly missing strava_id for:", len(missingstrava), "---------")
    for activity in missingstrava:
        candidate = bestmatch(
            {"distance": activity.distance, "date": activity.date}, "Strava"
        )
        if candidate:
            print("Strava", candidate.strava_id, "was lonely! Found a match.")
            activity.strava_id = candidate.strava_id
            activity.save()
    missingstrava = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.strava_id == ""
    )
    print(
        "--------- Main is now happily only missing strava_id for:",
        len(missingstrava),
        "---------",
    )


    # Fill in the missing file IDs from File using ~match.  How many are missing?
    missingfiles = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main",
        fitler.ActivityMetadata.original_filename is None,
    )
    print("--------- Main is sadly missing file for:", len(missingfiles), "---------")
    for activity in missingfiles:
        candidate = bestmatch(
            {"distance": activity.distance, "date": activity.date}, "File"
        )
        if candidate:
            print("File", candidate.original_filename, "was lonely! Found a match.")
            activity.original_filename = candidate.original_filename
            activity.save()
    print(
        "--------- Main is now happily only missing file for:",
        len(missingfiles),
        "---------",
    )


    # Fill in the missing garmin IDs from Garmin using ~match.
    # How many are missing?
    missinggarmin = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main", fitler.ActivityMetadata.garmin_id is None
    )
    print("--------- Main is missing garmin_id for:", len(missinggarmin), "---------")


    # Fill in the missing RidewithGPS IDs from RidewithGPS using ~match.
    # How many are missing?
    missingridewithgps = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main",
        fitler.ActivityMetadata.ridewithgps_id is None,
    )
    print(
        "--------- Main is sadly missing ridewithgps_id for:",
        len(missingridewithgps),
        "---------",
    )
    for activity in missingridewithgps:
        candidate = bestmatch(
            {"distance": activity.distance, "date": activity.date}, "RideWithGPS"
        )
        if candidate:
            print("RideWithGPS", candidate.ridewithgps_id, "was lonely! Found a match.")
            activity.ridewithgps_id = candidate.ridewithgps_id
            activity.save()
    missingridewithgps = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main",
        fitler.ActivityMetadata.ridewithgps_id is None,
    )
    print(
        "--------- Main is now happily only missing ridewithgps_id for:",
        len(missingridewithgps),
        "---------",
    )


    # Figure out which things in RideWithGPS need Gear and Names updated
    ridewithgps_gear = ridewithgpsbits.get_gear()
    rides = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main",
        fitler.ActivityMetadata.ridewithgps_id is not None,
    )
    for ride in rides:
        ridewithgps_ride = fitler.ActivityMetadata.select().where(
            fitler.ActivityMetadata.source == "RideWithGPS",
            fitler.ActivityMetadata.ridewithgps_id == ride.ridewithgps_id,
        )[0]
        if ride.equipment != ridewithgps_ride.equipment:
            print(
                "RideWithGPS",
                ridewithgps_ride.ridewithgps_id,
                "Needs gear updated from",
                ridewithgps_ride.equipment,
                "to",
                ride.equipment,
                "a.k.a.",
                list(ridewithgps_gear.keys())[
                    list(ridewithgps_gear.values()).index(ride.equipment)
                ],
            )
            # ridewithgpsbits.set_trip_gear(
            #     ridewithgps_ride.ridewithgps_id,
            #     list(ridewithgps_gear.keys())[list(ridewithgps_gear.values()).index(ride.equipment)]
            # )
        if ride.notes != ridewithgps_ride.notes:
            print(
                "RideWithGPS",
                ridewithgps_ride.ridewithgps_id,
                "Needs name updated from",
                ridewithgps_ride.notes,
                "to",
                ride.notes,
            )
            # ridewithgpsbits.set_trip_name(
            #     ridewithgps_ride.ridewithgps_id,
            #     ride.notes
            # )


    # For activities not in RideWithGPS, upload them! Careful.
    # Once this runs, you'll need to rm the sqllite db and rerun from
    # scratch to sync everything up.
    rides = fitler.ActivityMetadata.select().where(
        fitler.ActivityMetadata.source == "Main",
        fitler.ActivityMetadata.ridewithgps_id is None,
        fitler.ActivityMetadata.original_filename is not None,
    )
    for ride in rides:
        print(ride.id, "is missing from RideWithGPS. Uploading:", ride.original_filename)
        # ridewithgpsbits.create_trip(
        #         os.path.join(
        #             '/Users/ckdake/Code/fitler/export_5850/activities',
        #             ride.original_filename
        #         )
        # )