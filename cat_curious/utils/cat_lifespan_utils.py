import logging
import requests
import os

from cat_curious.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

def get_cat_lifespan(breed: str) -> int:
    """
    Fetch the estimated lifespan for a specific cat breed from TheCatAPI.

    Args:
        breed (str): The breed ID of the cat to get lifespan information for.

    Returns:
        int: Estimated lifespan of the breed, or raises an error if data is not available.

    Raises:
        RuntimeError: If no breed information is received from the API or if there is an error with the API request.
    """
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={os.getenv('KEY')}"
    try:
        logger.info("Requesting lifespan for breed '%s' from %s", breed, url)
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        logger.info("Response Status Code: %d", response.status_code)
        logger.info("Raw API Response: %s", response.text)
        response.raise_for_status()
        data = response.json()
    
        if isinstance(data, list) and len(data) > 0 and "life_span" in data[0]:
            lifespan = data[0]["life_span"]
            logger.info("Lifespan for breed '%s': %s years", breed, lifespan)
            return lifespan, data
        
        logger.error("No lifespan information received for breed '%s'. Response: %s", breed, data)
        raise RuntimeError(f"No breed lifespan information received for breed '{breed}'.")

    except requests.exceptions.Timeout:
        logger.error("Request to TheCatAPI timed out.")
        raise RuntimeError("Request to TheCatAPI timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to TheCatAPI failed: %s", e)
        raise RuntimeError("Request to TheCatAPI failed: %s" % e)

    except Exception as e:
        logger.error("Error retrieving cat lifespan: %s", e, exc_info=True)
        raise RuntimeError(f"Error retrieving cat lifespan: {e}")
