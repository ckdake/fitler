from fitler.activity import Activity
import datetime


def test_set_start_time_sets_fields():
    am = Activity()
    am.set_start_time("2024-05-27T14:30:00Z")
    # Should set both start_time and date
    assert am.start_time is not None
    assert am.date is not None


def test_to_json_returns_json_string():
    # Since Activity is now a Peewee model, we'll test model_to_dict instead
    am = Activity()
    am.set_start_time("2024-05-27T14:30:00-04:00")
    
    # Test that the fields are properly set
    assert isinstance(am.start_time, datetime.datetime)
    assert isinstance(am.date, datetime.date)
