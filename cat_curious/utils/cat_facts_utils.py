import logging
import requests

from cat_curious.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


def get_random_cat_facts(num_facts: int) -> list:
    """
    Fetches a certain number of random cat facts from the Cat Facts API. 

    Args:
        num_facts (int): The number of cat facts to retrieve.

    Returns:
        list: The list of random cat facts.

    Raises:
        RuntimeError: If we receive an invalid response or if the API Call fails/times out.
    """
    if num_facts <= 0:
        raise ValueError("Number of cat facts must be a positive integer.")

    url = f"https://catfact.ninja/facts?limit={num_facts}"

    try:
        # Log the request to Cat Facts API
        logger.info("Fetching %d random cat facts from %s", num_facts, url)

        response = requests.get(url, timeout=5)

        # Check if the request was successful
        response.raise_for_status()

        # Parse the response JSON
        data = response.json()

        if "data" not in data:
            raise ValueError("Invalid response from Cat Facts API: %s" % data)

        facts = [fact["fact"] for fact in data["data"]]

        logger.info("Received %d cat facts successfully.", len(facts))
        return facts

    except requests.exceptions.Timeout:
        logger.error("Request to Cat Facts API timed out.")
        raise RuntimeError("Request to Cat Facts API timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to Cat Facts API failed: %s", e)
        raise RuntimeError("Request to Cat Facts API failed: %s" % e)
