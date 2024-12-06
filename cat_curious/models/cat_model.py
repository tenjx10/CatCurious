from dataclasses import dataclass
import logging
import os
import sqlite3
from typing import Any

from cat_curious.utils.sql_utils import get_db_connection
from cat_curious.utils.logger import configure_logger
from cat_curious.utils.cat_affection_utils import get_affection_level
from cat_curious.utils.cat_info_utils import cat_info


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Cat:
    id: int
    name: str
    breed: str
    age: int
    weight: int

    def __post_init__(self):
        if self.breed not in ['abys', 'beng', 'chau','drex','emau','hbro','java','khao','lape','mala']:
            raise ValueError("not a valid breed")
        if self.age < 0:
            raise ValueError("Age must be a positive value.")
        if self.weight <= 0:
            raise ValueError("Weight must be a positive value.")


def create_cat(name: str, breed: str, age: int, weight: int) -> None:
    """
    Adds a new cat to the database.

    Args:
        name (str): Name of the cat.
        breed (str): Breed of the cat.
        age (int): Age of the cat in years.
        weight (int): Weight of the cat in kilograms.

    Raises:
        ValueError: If the breed, age, or weight is invalid or already exists in the database.
        sqlite3.Error: If a database error occurs.
    """
    if breed not in ['abys', 'beng', 'chau','drex','emau','hbro','java','khao','lape','mala']:
        raise ValueError(f"Invalid breed : {breed}.")
    if not isinstance(age, (int, float)) or age < 0:
        raise ValueError(f"Invalid age: {age}. Age must be a positive number.")
    if not isinstance(weight, (int, float)) or weight <= 0:
        raise ValueError(f"Invalid weight: {weight}. Weight must be a positive number.")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cats (name, breed, age, weight)
                VALUES (?, ?, ?, ?)
            """, (name, breed, age, weight))
            conn.commit()

            logger.info("Cat successfully added to the database: %s", name)

    except sqlite3.IntegrityError:
        logger.error("Duplicate cat name: %s", name)
        raise ValueError(f"Cat with name '{name}' already exists")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def clear_cats() -> None:
    """
    Recreates the cats table, effectively deleting all cats.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_cat_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Cats cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing cats: %s", str(e))
        raise e

def delete_cat(cat_id: int) -> None:
    """
    Marks a cat as deleted in the database.

    Args:
        cat_id (int): The unique ID of the cat to delete.

    Raises:
        ValueError: If the cat has already been deleted or doesn't exist.
        sqlite3.Error: If a database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM cats WHERE id = ?", (cat_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Cat with ID %s has already been deleted", cat_id)
                    raise ValueError(f"Cat with ID {cat_id} has been deleted")
            except TypeError:
                logger.info("Cat with ID %s not found", cat_id)
                raise ValueError(f"Cat with ID {cat_id} not found")

            cursor.execute("UPDATE cats SET deleted = TRUE WHERE id = ?", (cat_id,))
            conn.commit()

            logger.info("Cat with ID %s marked as deleted.", cat_id)

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_cat_by_id(cat_id: int) -> Cat:
    """
    Fetches a cat by its unique ID from the database.

    Args:
        cat_id (int): The unique ID of the cat.

    Returns:
        Cat: The cat object with the specified ID.

    Raises:
        ValueError: If the cat doesn't exist or has been deleted.
        sqlite3.Error: If a database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, breed, age, weight, deleted FROM cats WHERE id = ?", (cat_id,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Cat with ID %s has been deleted", cat_id)
                    raise ValueError(f"Cat with ID {cat_id} has been deleted")
                return Cat(id=row[0], name=row[1], breed=row[2], age=row[3], weight=row[4])
            else:
                logger.info("Cat with ID %s not found", cat_id)
                raise ValueError(f"Cat with ID {cat_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_cat_by_name(cat_name: str) -> Cat:
    """
    Fetches a cat by its name from the database.

    Args:
        cat_name (str): The name of the cat.

    Returns:
        Cat: The cat object with the specified name.

    Raises:
        ValueError: If the cat doesn't exist or has been deleted.
        sqlite3.Error: If a database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, breed, age, weight, deleted FROM cats WHERE cat = ?", (cat_name,))
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Cat with name %s has been deleted", cat_name)
                    raise ValueError(f"Cat with name {cat_name} has been deleted")
                return Cat(id=row[0], name=row[1], breed=row[2], age=row[3], weight=row[4])
            else:
                logger.info("Cat with name %s not found", cat_name)
                raise ValueError(f"Cat with name {cat_name} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e

def get_cat_info(cat_breed: str) -> str:
    """
    Fetches the description of a cat based on breed using an external API.
    
    Args:
        cat_breed (str): The breed of the cat.
    
    Returns:
        str: description of breed
    
    Raises:
        ValueError: If the breed is invalid or the description could not be retrieved.
    """
    try:
        if cat_breed not in ['abys', 'beng', 'chau', 'drex', 'emau', 'hbro', 'java', 'khao', 'lape', 'mala']:
            raise ValueError(f"Invalid breed: {cat_breed}.")
        
        info = cat_info(cat_breed)
        
        if not isinstance(info, str):
            raise ValueError(f"Description for breed '{cat_breed}' could not be retrieved.")
        
        logger.info("Fetched description for breed %s: %s", cat_breed, info)
        return info
    
    except Exception as e:
        logger.error("Error fetching description for breed %s: %s", cat_breed, str(e))
        raise
    

def get_cat_affection(cat_breed: str) -> int:
    """
    Fetches the affection level of a cat based on breed using an external API.
    
    Args:
        cat_breed (str): The breed of the cat.
    
    Returns:
        int: Affection level of the specified breed.
    
    Raises:
        ValueError: If the breed is invalid or affection level could not be retrieved.
    """
    try:
        if cat_breed not in ['abys', 'beng', 'chau', 'drex', 'emau', 'hbro', 'java', 'khao', 'lape', 'mala']:
            raise ValueError(f"Invalid breed: {cat_breed}.")
        
        affection_level = get_affection_level(cat_breed)
        
        if not isinstance(affection_level, int):
            raise ValueError(f"Affection level for breed '{cat_breed}' could not be retrieved.")
        
        logger.info("Fetched affection level for breed %s: %d", cat_breed, affection_level)
        return affection_level
    
    except Exception as e:
        logger.error("Error fetching affection level for breed %s: %s", cat_breed, str(e))
        raise
