import os
import stravaio

auth = stravaio.strava_oauth2(
    client_id=os.environ["STRAVA_CLIENT_ID"],
    client_secret=os.environ["STRAVA_CLIENT_SECRET"],
)

print(f"run: `export STRAVA_ACCESS_TOKEN={auth['access_token']}``")
