import pytest
import requests
import os

from cat_curious.utils.cat_lifespan_utils import get_cat_lifespan

MOCK_BREED = "siam"
MOCK_LIFESPAN = "12 - 15 years"

@pytest.fixture
def mock_cat_api_lifespan(mocker):
    """Mock TheCatAPI response for lifespan."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"breeds": [{"life_span": MOCK_LIFESPAN}]}
    ]
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_cat_lifespan_success(mock_cat_api_lifespan):
    """Test successful retrieval of cat lifespan."""
    result = get_cat_lifespan(MOCK_BREED)

    # Assert the returned value matches the mock
    assert result == MOCK_LIFESPAN, f"Expected lifespan {MOCK_LIFESPAN}, but got {result}"

    # Ensure the correct URL was called
    requests.get.assert_called_once_with(
        f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={MOCK_BREED}&api_key={os.getenv('KEY')}", timeout=5
    )

def test_get_cat_lifespan_timeout(mocker):
    """Test timeout during API call."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to TheCatAPI timed out."):
        get_cat_lifespan(MOCK_BREED)

def test_get_cat_lifespan_request_failure(mocker):
    """Test failure due to request error."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to TheCatAPI failed: Connection error"):
        get_cat_lifespan(MOCK_BREED)

def test_get_cat_lifespan_no_data(mock_cat_api_lifespan):
    """Test API response with no breed data."""
    mock_cat_api_lifespan.json.return_value = [{"breeds": []}]

    with pytest.raises(RuntimeError, match="No breed information received from API."):
        get_cat_lifespan(MOCK_BREED)

def test_get_cat_lifespan_invalid_response(mock_cat_api_lifespan):
    """Test invalid response structure."""
    mock_cat_api_lifespan.json.return_value = [{"not_breeds": [{"life_span": MOCK_LIFESPAN}]}]

    with pytest.raises(RuntimeError, match="No breed information received from API."):
        get_cat_lifespan(MOCK_BREED)
