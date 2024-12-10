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

def test_create_user(Users, sample_user, mock_cursor, mocker):
    """Test creating a new user with a unique username."""

    # Mock the generate_hashed_password method to return predictable values
    mock_generate_hashed_password = mocker.patch.object(Users, 'generate_hashed_password', return_value=("mocked_salt", "mocked_hashed_password"))

    # Call the create_user method
    Users.create_user(**sample_user)

    expected_query = normalize_whitespace("""
        INSERT INTO users (username, salt, password)
        VALUES (?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (sample_user["username"], "mocked_salt", "mocked_hashed_password")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

    # Verify that the generate_hashed_password method was called once with the password
    mock_generate_hashed_password.assert_called_once_with(sample_user["password"])




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

def test_check_password_correct(Users, sample_user, mock_cursor, mocker):
    """Test checking the correct password."""

    # Mock the database to return the correct salt and password for the user
    mock_cursor.fetchone.return_value = ("mocked_salt", "mocked_hashed_password")

    # Mock the hash generation for the password
    # Ensure the hash generated for password + salt matches the stored hash
    mocker.patch("hashlib.sha256", return_value=mocker.Mock(hexdigest=mocker.Mock(return_value="mocked_hashed_password")))

    # Create the user in the database (assumed behavior of the create_user function)
    Users.create_user(**sample_user)

    # Verify that the password matches by calling check_password
    result = Users.check_password(sample_user["username"], sample_user["password"])

    # Assert that the result is True because the password should match
    assert result is True, f"Password for user {sample_user['username']} should match."



def test_check_password_incorrect(Users, sample_user, mock_cursor, mocker):
    """Test checking an incorrect password."""
    # Create the user in the database (assumed behavior of the create_user function)
    Users.create_user(**sample_user)

    # Mock the database to return the correct salt and password for the user
    mock_cursor.fetchone.return_value = ("mocked_salt", "mocked_hashed_password")

    # Mock the hash generation for the incorrect password
    mocker.patch("hashlib.sha256", return_value=mocker.Mock(hexdigest=mocker.Mock(return_value="incorrect_hashed_password")))

    # Verify the password check returns False for incorrect password
    assert Users.check_password(sample_user["username"], "wrongpassword") is False, "Password should not match."


def test_check_password_user_not_found(Users, mock_cursor):
    """Test checking password for a non-existent user."""
    mock_cursor.fetchone.return_value = None  # Simulate user not found
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.check_password("nonexistentuser", "password")


##########################################################
# Update Password
##########################################################

def test_update_password(Users, sample_user, mock_cursor, mocker):
    """Test updating the password for an existing user."""
    # Create the user with the initial password
    Users.create_user(**sample_user)
    
    new_password = "newpassword456"

    # Mock the generate_hashed_password method to return predictable values for the new password
    mocker.patch.object(Users, 'generate_hashed_password', return_value=("new_mocked_salt", "new_mocked_hashed_password"))
    
    # Call the update_password method to update the user's password
    Users.update_password(sample_user["username"], new_password)
    
    # Normalize whitespace in both the expected and actual queries
    expected_query = normalize_whitespace("""
        UPDATE users SET salt = ?, password = ? WHERE username = ?
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Verify that the update query was executed with the correct values
    assert actual_query == expected_query, f"Expected query: {expected_query}, but got: {actual_query}"

    # Verify that the arguments used in the query match
    expected_arguments = ('new_mocked_salt', 'new_mocked_hashed_password', sample_user["username"])
    actual_arguments = mock_cursor.execute.call_args[0][1]
    assert actual_arguments == expected_arguments, f"Expected arguments: {expected_arguments}, but got: {actual_arguments}"
    


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
    mock_cursor.fetchone.return_value = (1, sample_user["username"], mock_cursor.return_value)
    
    user_id = Users.get_id_by_username(sample_user["username"])
    
    assert user_id == 1, "Retrieved ID should match the user's ID."

def test_get_id_by_username_user_not_found(Users, mock_cursor):
    """
    Test failure when retrieving a non-existent user's ID by their username.
    """
    mock_cursor.fetchone.return_value = None  # Simulate user not found
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.get_id_by_username("nonexistentuser")
