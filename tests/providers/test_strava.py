import pytest
from fitler.providers.strava.strava_provider import StravaProvider

@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("Altra Kayenta 2020 Black/Lime", "2020 Altra Kayenta"),
        ("Altra Lone Peak 2018 Altra Lone Peak", "2018 Altra Lone Peak"),
        ("Specialized Stumpjumper 2019 Carbon", "2019 Specialized Stumpjumper"),
        ("NoYearBikeName", "NoYearBikeName"),
        ("Trek 2022", "2022 Trek"),
        ("2021 Giant Propel Advanced", "2021 Giant Propel Advanced"),
    ]
)
def test_normalize_strava_gear_name(input_name, expected):
    assert StravaProvider._normalize_strava_gear_name(input_name) == expected