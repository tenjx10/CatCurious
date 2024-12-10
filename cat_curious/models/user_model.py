import hashlib
import logging
import os
import sqlite3

from cat_curious.utils.logger import configure_logger
from cat_curious.utils.sql_utils import get_db_connection


logger = logging.getLogger(__name__)
configure_logger(logger)


class Users():
    id = int
    username = str
    salt = str
    password = str

    def __post_init__(self):
        logger.info(f"User {self.username} initialized with a hashed password.")

def generate_hashed_password(password: str) -> tuple[str, str]:
    """
    Generates a salted, hashed password.

    Args:
        password (str): The password to hash.

    Returns:
        tuple: A tuple containing the salt and hashed password.
    """
    salt = os.urandom(16).hex()
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    return salt, hashed_password
    
  
def create_user(cls, username: str, password: str) -> None:
        """
        Create a new user with a salted, hashed password.

        Args:
            username (str): The username of the user.
            password (str): The password to hash and store.

        Raises:
            ValueError: If a user with the username already exists.
        """
        salt, hashed_password = cls._generate_hashed_password(password)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, salt, password)
                    VALUES (?, ?, ?)
                """, (username, salt, hashed_password))
                conn.commit()
                logger.info("User successfully added to the database: %s", username)
        except sqlite3.IntegrityError:
            logger.error("Duplicate username: %s", username)
            raise ValueError(f"User with username '{username}' already exists")
        except sqlite3.Error as e:
            logger.error("Database error: %s", str(e))
            raise


def check_password(cls, username: str, password: str) -> bool:
        """
        Check if a given password matches the stored password for a user.

        Args:
            username (str): The username of the user.
            password (str): The password to check.

        Returns:
            bool: True if the password is correct, False otherwise.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")
        hashed_password = hashlib.sha256((password + user.salt).encode()).hexdigest()
        return hashed_password == user.password


def delete_user(cls, username: str) -> None:
        """
        Delete a user from the database.

        Args:
            username (str): The username of the user to delete.

        Raises:
            ValueError: If the user does not exist.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                if cursor.rowcount == 0:
                    logger.info("User %s not found", username)
                    raise ValueError(f"User {username} not found")
                conn.commit()
                logger.info("User %s deleted successfully", username)
        except sqlite3.Error as e:
            logger.error("Database error: %s", str(e))
            raise


def get_id_by_username(cls, username: str) -> int:
        """
        Retrieve the ID of a user by username.

        Args:
            username (str): The username of the user.

        Returns:
            int: The ID of the user.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")
        return user.id


def update_password(cls, username: str, new_password: str) -> None:
        """
        Update the password for a user.

        Args:
            username (str): The username of the user.
            new_password (str): The new password to set.

        Raises:
            ValueError: If the user does not exist.
        """
        salt, hashed_password = cls._generate_hashed_password(new_password)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET salt = ?, password = ? WHERE username = ?
                """, (salt, hashed_password, username))
                if cursor.rowcount == 0:
                    logger.info("User %s not found", username)
                    raise ValueError(f"User {username} not found")
                conn.commit()
                logger.info("Password updated successfully for user: %s", username)
        except sqlite3.Error as e:
            logger.error("Database error: %s", str(e))
            raise