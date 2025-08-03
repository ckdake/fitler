import pytest
from unittest.mock import Mock, MagicMock
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
    ],
)
def test_normalize_strava_gear_name(input_name, expected):
    assert StravaProvider._normalize_strava_gear_name(input_name) == expected


class TestStravaProviderUpdate:
    """Test Strava provider update_activity method."""

    def test_update_activity_name_success(self):
        """Test successful name update via Strava API."""
        # Mock the stravalib client
        mock_client = Mock()
        mock_client.update_activity = Mock()

        # Create provider with mocked client
        provider = StravaProvider(
            token="test_token", refresh_token="test_refresh", token_expires="999999999"
        )
        provider.client = mock_client

        # Test data
        activity_data = {"strava_id": "12345", "name": "Updated Activity Name"}

        # Call update_activity
        result = provider.update_activity(activity_data)

        # Verify the result
        assert result is True

        # Verify the API was called correctly
        mock_client.update_activity.assert_called_once_with(
            activity_id=12345, name="Updated Activity Name"
        )

    def test_update_activity_multiple_fields(self):
        """Test updating multiple fields via Strava API."""
        # Mock the stravalib client
        mock_client = Mock()
        mock_client.update_activity = Mock()

        # Create provider with mocked client
        provider = StravaProvider(
            token="test_token", refresh_token="test_refresh", token_expires="999999999"
        )
        provider.client = mock_client

        # Test data with multiple fields
        activity_data = {
            "strava_id": "67890",
            "name": "New Name",
            "description": "New description",
        }

        # Call update_activity
        result = provider.update_activity(activity_data)

        # Verify the result
        assert result is True

        # Verify the API was called with all fields except strava_id
        mock_client.update_activity.assert_called_once_with(
            activity_id=67890, name="New Name", description="New description"
        )

    def test_update_activity_api_failure(self):
        """Test handling of API failure during update."""
        # Mock the stravalib client to raise an exception
        mock_client = Mock()
        mock_client.update_activity = Mock(side_effect=Exception("API Error"))

        # Create provider with mocked client
        provider = StravaProvider(
            token="test_token", refresh_token="test_refresh", token_expires="999999999"
        )
        provider.client = mock_client

        # Test data
        activity_data = {"strava_id": "12345", "name": "Updated Name"}

        # Call update_activity and expect it to handle the exception
        result = provider.update_activity(activity_data)

        # Verify the result is False due to the exception
        assert result is False

        # Verify the API was called
        mock_client.update_activity.assert_called_once()

    def test_update_activity_removes_provider_id(self):
        """Test that strava_id is removed from the data sent to API."""
        # Mock the stravalib client
        mock_client = Mock()
        mock_client.update_activity = Mock()

        # Create provider with mocked client
        provider = StravaProvider(
            token="test_token", refresh_token="test_refresh", token_expires="999999999"
        )
        provider.client = mock_client

        # Test data
        activity_data = {
            "strava_id": "12345",
            "name": "Test Name",
            "some_other_field": "some_value",
        }

        # Call update_activity
        provider.update_activity(activity_data)

        # Verify that strava_id was not passed to the API
        # but other fields were passed
        mock_client.update_activity.assert_called_once_with(
            activity_id=12345, name="Test Name", some_other_field="some_value"
        )
