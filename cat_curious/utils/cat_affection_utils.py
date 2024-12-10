import logging
import requests
import os


from cat_curious.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

def get_affection_level(breed: str) -> int:
    """
    Retrieves the affection level for a specified cat breed using TheCatAPI.

    Args:
        breed (str): The breed identifier for which to fetch the affection level.

    Returns:
        int: The affection level of the specified breed, as provided by TheCatAPI.

    Raises:
        RuntimeError: If no breed information is returned by the API or if there is an error in the request.
    """
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={os.getenv('KEY')}"
    try:
        logger.info("Fetching breed information from %s", url)

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "breeds" in data[0] and data[0]["breeds"]:
            affection_level = data[0]["breeds"][0]["affection_level"]
            logger.info("Received affection level: %d", affection_level)
            return affection_level
        else:
            raise RuntimeError("No breed information received from API.")

    except requests.exceptions.Timeout:
        logger.error("Request to TheCatAPI timed out.")
        raise RuntimeError("Request to TheCatAPI timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to TheCatAPI failed: %s", e)
        raise RuntimeError("Request to TheCatAPI failed: %s" % e)
