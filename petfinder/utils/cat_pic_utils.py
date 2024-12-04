import logging
import requests

from petfinder.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


def get_cat_pic(breed: str) -> str:
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
    try:
        logger.info("Fetching cat picture from %s", url)

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data:
            cat_pic_url = data[0]["url"]
            logger.info("Received cat picture URL: %s", cat_pic_url)
            return cat_pic_url
        else:
            raise RuntimeError("No data received from API.")

    except requests.exceptions.Timeout:
        logger.error("Request to TheCatAPI timed out.")
        raise RuntimeError("Request to TheCatAPI timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to TheCatAPI failed: %s", e)
        raise RuntimeError("Request to TheCatAPI failed: %s" % e)
