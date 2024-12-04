import logging
import requests

from petfinder.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

def get_affection_level(breed: str) -> int:
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
    try:
        logger.info("Fetching breed information from %s", url)

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "breeds" in data[0]:
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
