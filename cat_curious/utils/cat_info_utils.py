import logging
import requests

from cat_curious.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

def get_cat_info(breed: str) -> str:
    """
    Fetches the description of a cat breed using TheCatAPI.
    
    Args:
        breed (str): The ID of the cat breed.
    
    Returns:
        str: Description of the cat breed.
    
    Raises:
        RuntimeError: If the request fails or data is missing.
    """
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
    try:
        logger.info("Fetching cat description from %s", url)

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "breeds" in data[0] and data[0]["breeds"]:
            description = data[0]["breeds"][0].get("description")
            if description:
                logger.info("Received description for breed '%s': %s", breed, description)
                return description
            else:
                raise RuntimeError(f"Description not found for breed '{breed}'.")
        else:
            raise RuntimeError("No data received from API.")

    except requests.exceptions.Timeout:
        logger.error("Request to TheCatAPI timed out.")
        raise RuntimeError("Request to TheCatAPI timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to TheCatAPI failed: %s", e)
        raise RuntimeError(f"Request to TheCatAPI failed: {e}")
