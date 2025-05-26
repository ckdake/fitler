from fitler.metadata import ActivityMetadata


def test_set_start_time_sets_fields():
    am = ActivityMetadata()
    am.set_start_time("2024-05-27T14:30:00Z")
    # Should set both start_time and date
    assert am.start_time.startswith("2024-05-27T")
    assert am.date == "2024-05-27"


def test_to_json_returns_json_string():
    am = ActivityMetadata()
    am.start_time = "2024-05-27T14:30:00-04:00"
    am.date = "2024-05-27"
    json_str = am.to_json()
    assert isinstance(json_str, str)
    assert '"start_time": "2024-05-27T14:30:00-04:00"' in json_str
    assert '"date": "2024-05-27"' in json_str
