import pytest
from unittest.mock import MagicMock, patch
from fitler.providers.ridewithgps import RideWithGPSProvider, Activity

@pytest.fixture
def mock_client():
    mock = MagicMock()
    mock.authenticate.return_value = {"id": 123}
    mock.user = {"id": 123}
    return mock

@pytest.fixture(autouse=True)
def patch_rwgps_activities(monkeypatch):
    """Patch RideWithGPSProvider.__init__ to not require env vars and set mock client."""
    def fake_init(self):
        self.client = MockRWGPSClient()
        self.userid = 123

    monkeypatch.setattr(RideWithGPSProvider, "__init__", fake_init)

def test_fetch_activities(monkeypatch, mock_client):
    mock_client.list.return_value = [
        {
            "id": 1,
            "departed_at": "2024-06-01T10:00:00Z",
            "distance": 10000,
            "name": "Morning Ride",
            "gear_id": "bike1",
        }
    ]
    monkeypatch.setattr(RideWithGPSProvider, "get_gear", lambda self: {"bike1": "Road Bike"})
    act = RideWithGPSProvider()
    activities = act.fetch_activities()
    assert len(activities) == 1
    assert activities[0].notes == "Morning Ride"
    assert activities[0].equipment == "Road Bike"

def test_create_activity(mock_client):
    mock_client.put.return_value = {"id": 42}
    act = RideWithGPSProvider()
    with patch("builtins.open", create=True):
        activity = Activity(source_file="fake.gpx")
        result = act.create_activity(activity)
    assert result == "42"
    mock_client.put.assert_called_once()

def test_get_activity_by_id(monkeypatch, mock_client):
    mock_client.get.return_value = {
        "id": 2,
        "departed_at": "2024-06-02T12:00:00Z",
        "distance": 5000,
        "name": "Lunch Ride",
        "gear_id": "bike2",
    }
    monkeypatch.setattr(RideWithGPSProvider, "get_gear", lambda self: {"bike2": "Gravel Bike"})
    act = RideWithGPSProvider()
    activity = act.get_activity_by_id(2)
    assert activity is not None
    assert activity.notes == "Lunch Ride"
    assert activity.equipment == "Gravel Bike"

def test_update_activity(mock_client):
    mock_client.put.return_value = {"name": "Updated Ride"}
    act = RideWithGPSProvider()
    activity = Activity(name="Updated Ride")
    result = act.update_activity(3, activity)
    assert result is True
    mock_client.put.assert_called_once()

def test_get_gear(mock_client):
    mock_client.list.return_value = [
        {"id": "bike1", "nickname": "Road Bike"},
        {"id": "bike2", "nickname": "Gravel Bike"},
    ]
    act = RideWithGPSProvider()
    gear = act.get_gear()
    assert gear == {"bike1": "Road Bike", "bike2": "Gravel Bike"}

def test_set_gear(mock_client):
    mock_client.put.return_value = {"gear_id": "bike1"}
    act = RideWithGPSProvider()
    result = act.set_gear("bike1", 4)
    assert result is True
    mock_client.put.assert_called_once()