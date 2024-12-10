import logging
import requests
import os

from cat_curious.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

def get_random_cat_image() -> str:
    """
    Fetch a random cat image from TheCatAPI.

    Args:
        none.

    Returns:
        str: URL of the random cat image, or raises an error if the request fails.

    Raises:
        RuntimeError: If the request to TheCatAPI fails or if no image is received from the API.
    """
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&api_key={os.getenv('KEY')}"
    try:
        logger.info("Fetching random cat image from %s", url)

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "url" in data[0]:
            cat_image_url = data[0]["url"]
            logger.info("Fetched random cat image URL: %s", cat_image_url)
            return cat_image_url
        else:
            raise RuntimeError("No cat image URL received from API.")

    except requests.exceptions.Timeout:
        logger.error("Request to TheCatAPI timed out.")
        raise RuntimeError("Request to TheCatAPI timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to TheCatAPI failed: %s", e)
        raise RuntimeError("Request to TheCatAPI failed: %s" % e)

    except Exception as e:
        logger.error("Error retrieving random cat image: %s", e)
        raise RuntimeError(f"Error retrieving random cat image: {e}")
