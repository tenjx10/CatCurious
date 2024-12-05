import pytest
import requests

import os
from dotenv import load_dotenv

from cat_curious.utils.cat_affection_utils import get_affection_level

MOCK_BREED = "drex"
MOCK_AFFECTION_LEVEL = 5


@pytest.fixture
def mock_cat_api(mocker):
    """Mock TheCatAPI response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"breeds": [{"affection_level": MOCK_AFFECTION_LEVEL}]}
    ]
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response


def test_get_affection_level_success(mock_cat_api):
    """Test successful retrieval of affection level."""
    result = get_affection_level(MOCK_BREED)

    # Assert the returned value matches the mock
    assert result == MOCK_AFFECTION_LEVEL, f"Expected affection level {MOCK_AFFECTION_LEVEL}, but got {result}"

    # Ensure the correct URL was called
    requests.get.assert_called_once_with(
        f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={MOCK_BREED}&api_key={os.getenv('KEY')}", timeout=5
    )


def test_get_affection_level_timeout(mocker):
    """Test timeout during API call."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to TheCatAPI timed out."):
        get_affection_level(MOCK_BREED)


def test_get_affection_level_request_failure(mocker):
    """Test failure due to request error."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to TheCatAPI failed: Connection error"):
        get_affection_level(MOCK_BREED)

def test_get_affection_level_no_data(mock_cat_api):
    """Test API response with no breed data."""
    mock_cat_api.json.return_value = [{"breeds": []}]

    with pytest.raises(RuntimeError, match="No breed information received from API."):
        get_affection_level(MOCK_BREED)


def test_get_affection_level_invalid_response(mock_cat_api):
    """Test invalid response structure."""
    mock_cat_api.json.return_value = [{"not_breeds": [{"affection_level": MOCK_AFFECTION_LEVEL}]}]

    with pytest.raises(RuntimeError, match="No breed information received from API."):
        get_affection_level(MOCK_BREED)
