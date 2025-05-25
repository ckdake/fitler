"""Defines our data model."""

import json
import dateparser
import pytz
from peewee import (
    SqliteDatabase,
    Model,
    DateTimeField,
    CharField,
    DecimalField,
    FloatField,
    IntegerField,
    DateField,
)

db = SqliteDatabase("metadata.sqlite3")


class ActivityMetadata(Model):
    start_time = DateTimeField(null=True)
    original_filename = CharField(null=True)
    date = DateField(null=True)
    activity_type = CharField(null=True)
    location_name = CharField(null=True)
    city = CharField(null=True)
    state = CharField(null=True)
    temperature = DecimalField(null=True)
    equipment = CharField(null=True)
    duration_hms = CharField(null=True)
    distance = FloatField(null=True)
    max_speed = DecimalField(null=True)
    avg_heart_rate = IntegerField(null=True)
    max_heart_rate = IntegerField(null=True)
    calories = IntegerField(null=True)
    max_elevation = IntegerField(null=True)
    total_elevation_gain = IntegerField(null=True)
    with_names = CharField(null=True)
    avg_cadence = IntegerField(null=True)
    strava_id = IntegerField(null=True)
    garmin_id = IntegerField(null=True)
    ridewithgps_id = IntegerField(null=True)
    notes = CharField(null=True)
    source = CharField(null=True)

    def set_start_time(self, datetimestring):
        timezone_datetime_obj = dateparser.parse(
            datetimestring,
            settings={"TIMEZONE": "GMT", "RETURN_AS_TIMEZONE_AWARE": True},
        ).astimezone(pytz.timezone("US/Eastern"))

        self.start_time = timezone_datetime_obj.replace(microsecond=0).isoformat()
        self.date = timezone_datetime_obj.strftime("%Y-%m-%d")

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    class Meta:
        database = db  # This model uses the "metadata.sqlite3" database

    @classmethod
    def migrate(self):
        db.connect()
        db.create_tables([ActivityMetadata])
        db.close()
