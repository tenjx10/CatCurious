import pytest
import requests
import os

from cat_curious.utils.cat_random_image_utils import get_random_cat_image

MOCK_IMAGE_URL = "https://cdn2.thecatapi.com/images/12345.jpg"

@pytest.fixture
def mock_cat_api_image(mocker):
    """Mock TheCatAPI response for random cat image."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"url": MOCK_IMAGE_URL}]
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_random_cat_image_success(mock_cat_api_image):
    """Test successful retrieval of random cat image URL."""
    result = get_random_cat_image()

    # Assert the returned value matches the mock
    assert result == MOCK_IMAGE_URL, f"Expected image URL {MOCK_IMAGE_URL}, but got {result}"

    # Ensure the correct URL was called
    requests.get.assert_called_once_with(
        f"https://api.thecatapi.com/v1/images/search?limit=1&api_key={os.getenv('KEY')}", timeout=5
    )

def test_get_random_cat_image_timeout(mocker):
    """Test timeout during API call."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to TheCatAPI timed out."):
        get_random_cat_image()

def test_get_random_cat_image_request_failure(mocker):
    """Test failure due to request error."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to TheCatAPI failed: Connection error"):
        get_random_cat_image()

def test_get_random_cat_image_no_data(mock_cat_api_image):
    """Test API response with no image data."""
    mock_cat_api_image.json.return_value = []

    with pytest.raises(RuntimeError, match="No cat image URL received from API."):
        get_random_cat_image()

def test_get_random_cat_image_invalid_response(mock_cat_api_image):
    """Test invalid response structure."""
    mock_cat_api_image.json.return_value = [{"not_url": MOCK_IMAGE_URL}]

    with pytest.raises(RuntimeError, match="Error retrieving random cat image: .*"):
        get_random_cat_image()
