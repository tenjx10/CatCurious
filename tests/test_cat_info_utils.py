import pytest
import requests
import os
from unittest.mock import patch

from cat_curious.utils.cat_info_utils import get_cat_info

MOCK_BREED = "drex"
MOCK_INFO = "The favourite perch of the Devon Rex is right at head level, on the shoulder of her favorite person. She takes a lively interest in everything that is going on and refuses to be left out of any activity. Count on her to stay as close to you as possible, occasionally communicating his opinions in a quiet voice. She loves people and welcomes the attentions of friends and family alike."

@pytest.fixture
def mock_cat_api(mocker):
    """Mock TheCatAPI response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"breeds": [{"description": MOCK_INFO}]}  # Correct key is 'description'
    ]
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_info_success(mock_cat_api):
    """Test successful retrieval of description."""
    result = get_cat_info(MOCK_BREED)

    # Assert the returned value matches the mock
    assert result == MOCK_INFO, f"Expected description {MOCK_INFO}, but got {result}"

    # Ensure the correct URL was called, including the mock API key
    api_key = os.getenv('KEY', 'fake-api-key')  # Use a default value if KEY isn't set
    requests.get.assert_called_once_with(
        f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={MOCK_BREED}&api_key={api_key}", timeout=5
    )

def test_get_info_timeout(mocker):
    """Test timeout during API call."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to TheCatAPI timed out."):
        get_cat_info(MOCK_BREED)

def test_get_info_request_failure(mocker):
    """Test failure due to request error."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to TheCatAPI failed: Connection error"):
        get_cat_info(MOCK_BREED)

def test_get_info_no_data(mock_cat_api):
    """Test API response with no breed data."""
    # Return an empty list for breeds to simulate missing breed data
    mock_cat_api.json.return_value = [{"breeds": []}]
    
    with pytest.raises(RuntimeError, match="No data received from API."):
        get_cat_info(MOCK_BREED)

def test_get_info_invalid_response(mock_cat_api):
    """Test invalid response structure."""
    # Simulate incorrect response structure
    mock_cat_api.json.return_value = [{"not_breeds": [{"description": MOCK_INFO}]}]

    with pytest.raises(RuntimeError, match="No data received from API."):
        get_cat_info(MOCK_BREED)

