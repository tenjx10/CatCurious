from contextlib import contextmanager
import re
import sqlite3
import pytest
from cat_curious.models.user_model import Users

@pytest.fixture
def Users():
    from cat_curious.models.user_model import Users
    return Users

@pytest.fixture
def sample_user():
    return {
        "username": "testuser",
        "password": "password123",
    }



def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("cat_curious.models.user_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


##########################################################
# User Creation
##########################################################

def test_create_user(Users, sample_user, mock_cursor):
    """Test creating a new user with a unique username."""
    Users.create_user(**sample_user)
    
    # Verify that the database insert query was executed
    mock_cursor.execute.assert_called_with("""
        INSERT INTO users (username, salt, password)
        VALUES (?, ?, ?)
    """, (sample_user["username"], mock_cursor.return_value, mock_cursor.return_value))  # Adjust as necessary
    
    # Verify the insert was committed
    mock_cursor.connection.commit.assert_called_once()

def test_create_duplicate_user(Users, sample_user, mock_cursor):
    """Test attempting to create a user with a duplicate username."""
    Users.create_user(**sample_user)
    
    # Simulate a duplicate username by raising an IntegrityError
    mock_cursor.execute.side_effect = sqlite3.IntegrityError
    with pytest.raises(ValueError, match="User with username 'testuser' already exists"):
        Users.create_user(**sample_user)


##########################################################
# User Authentication
##########################################################

def test_check_password_correct(Users, sample_user, mock_cursor):
    """Test checking the correct password."""
    Users.create_user(**sample_user)
    
    # Mock the database to return the correct hashed password and salt for the user
    mock_cursor.fetchone.return_value = (sample_user["username"], sample_user["salt"], mock_cursor.return_value)
    
    assert Users.check_password(sample_user["username"], sample_user["password"]) is True, "Password should match."

def test_check_password_incorrect(Users, sample_user, mock_cursor):
    """Test checking an incorrect password."""
    Users.create_user(**sample_user)
    
    # Mock the database to return the correct salt but incorrect hashed password for the user
    mock_cursor.fetchone.return_value = (sample_user["username"], sample_user["salt"], mock_cursor.return_value)
    
    assert Users.check_password(sample_user["username"], "wrongpassword") is False, "Password should not match."

def test_check_password_user_not_found(Users, mock_cursor):
    """Test checking password for a non-existent user."""
    mock_cursor.fetchone.return_value = None  # Simulate user not found
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.check_password("nonexistentuser", "password")


##########################################################
# Update Password
##########################################################

def test_update_password(Users, sample_user, mock_cursor):
    """Test updating the password for an existing user."""
    Users.create_user(**sample_user)
    
    new_password = "newpassword456"
    Users.update_password(sample_user["username"], new_password)
    
    # Verify that the update query was executed
    mock_cursor.execute.assert_called_with("""
        UPDATE users SET salt = ?, password = ? WHERE username = ?
    """, (mock_cursor.return_value, mock_cursor.return_value, sample_user["username"]))
    
    mock_cursor.connection.commit.assert_called_once()

def test_update_password_user_not_found(Users, mock_cursor):
    """Test updating the password for a non-existent user."""
    mock_cursor.rowcount = 0  # Simulate no user found
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.update_password("nonexistentuser", "newpassword")


##########################################################
# Delete User
##########################################################

def test_delete_user(Users, sample_user, mock_cursor):
    """Test deleting an existing user."""
    Users.create_user(**sample_user)
    Users.delete_user(sample_user["username"])
    
    # Verify that the delete query was executed
    mock_cursor.execute.assert_called_with("DELETE FROM users WHERE username = ?", (sample_user["username"],))
    mock_cursor.connection.commit.assert_called_once()

def test_delete_user_not_found(Users, sample_user, mock_cursor):
    """Test deleting a non-existent user."""
    mock_cursor.rowcount = 0  # Simulate no user found
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.delete_user("nonexistentuser")


##########################################################
# Get User
##########################################################

def test_get_id_by_username(Users, sample_user, mock_cursor):
    """
    Test successfully retrieving a user's ID by their username.
    """
    Users.create_user(**sample_user)
    
    # Mock the return of the ID
    mock_cursor.fetchone.return_value = (1, sample_user["username"], sample_user["salt"], mock_cursor.return_value)
    
    user_id = Users.get_id_by_username(sample_user["username"])
    
    assert user_id == 1, "Retrieved ID should match the user's ID."

def test_get_id_by_username_user_not_found(Users, mock_cursor):
    """
    Test failure when retrieving a non-existent user's ID by their username.
    """
    mock_cursor.fetchone.return_value = None  # Simulate user not found
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.get_id_by_username("nonexistentuser")
