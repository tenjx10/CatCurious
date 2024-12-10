from contextlib import contextmanager
import re
import sqlite3

import pytest
from pytest_mock import mocker

from cat_curious.models.cat_model import (
    Cat,
    create_cat,
    clear_cats,
    delete_cat,
    get_cat_by_id,
    get_cat_by_name,
    get_cat_info,
    get_cat_affection,
)

######################################################
#
#    Fixtures
#
######################################################

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

    mocker.patch("cat_curious.models.cat_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_cat(mock_cursor):
    """Test creating a new cat in the catalog."""

    # Call the function to create a new cat 
    create_cat(name="Mittens", breed="beng", age=3, weight=10)

    expected_query = normalize_whitespace("""
        INSERT INTO cats (name, breed, age, weight)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Mittens", "beng", 3, 10)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_cat_duplicate(mock_cursor):
    """Test creating a cat with a duplicate name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: cats.name")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Cat with name 'Mittens' already exists"):
        create_cat(name="Mittens", breed="beng", age=3, weight=10)

def test_create_cat_invalid_weight():
    """Test error when trying to create a cat with an invalid weight (e.g., negative weight)"""

    # Attempt to create a cat with a negative weight
    with pytest.raises(ValueError, match="Invalid weight: -10. Weight must be a positive number."):
        create_cat(name="Mittens", breed="beng", age=3, weight=-10)

    # Attempt to create a cat with a non-integer weight
    with pytest.raises(ValueError, match="Invalid weight: ten. Weight must be a positive number."):
        create_cat(name="Mittens", breed="beng", age=3, weight="ten")

def test_create_cat_invalid_age():
    """Test error when trying to create a cat with an invalid age (e.g., non-integer)."""

    # Attempt to create a cat with a negative age
    with pytest.raises(ValueError, match="Invalid age: -3. Age must be a positive number."):
        create_cat(name="Mittens", breed="beng", age=-3, weight=10)

    # Attempt to create a cat with a non-integer age
    with pytest.raises(ValueError, match="Invalid age: three. Age must be a positive number."):
        create_cat(name="Mittens", breed="beng", age="three", weight=10)

def test_create_cat_invalid_breed():
    """Test error when trying to create a cat with an invalid breed (e.g., not breed list)"""

    # Attempt to create a cat with an invalid breed
    with pytest.raises(ValueError, match="Invalid breed : cool."):
        create_cat(name="Mittens", breed="cool", age=3, weight=-10)

def test_delete_cat(mock_cursor):
    """Test soft deleting a cat from the catalog by cat ID."""

    # Simulate that the song exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_song function
    delete_cat(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM cats WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE cats SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_cat_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent cat."""

    # Simulate that no cat exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent cat
    with pytest.raises(ValueError, match="Cat with ID 999 not found"):
        delete_cat(999)

def test_delete_cat_already_deleted(mock_cursor):
    """Test error when trying to delete a cat that's already marked as deleted."""

    # Simulate that the song exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a song that's already been deleted
    with pytest.raises(ValueError, match="Cat with ID 999 has been deleted"):
        delete_cat(999)

def test_clear_cats(mock_cursor, mocker):
    """Test clearing the entire cat catalog (removes all cats)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_cat_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_cats()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_cat_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Get Cat
#
######################################################

def test_get_cat_by_id(mock_cursor):
    # Simulate that the cat exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Mittens", "beng", 3, 10, False)

    # Call the function and check the result
    result = get_cat_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Cat(1, "Mittens", "beng", 3, 10)

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, name, breed, age, weight, deleted FROM cats WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_cat_by_id_bad_id(mock_cursor):
    # Simulate that no cat exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the cat is not found
    with pytest.raises(ValueError, match="Cat with ID 999 not found"):
        get_cat_by_id(999)

def test_get_cat_by_deleted_id(mock_cursor):
    # Simulate that the cat has been deleted
    mock_cursor.fetchone.return_value = (1,"Mittens","beng",3,10,True)

    # Expect a ValueError when the cat is not found
    with pytest.raises(ValueError, match="Cat with ID 1 has been deleted"):
        get_cat_by_id(1)
    
def test_get_cat_by_name(mock_cursor):
    # Simulate that the cat exists (name = Mittens)
    mock_cursor.fetchone.return_value = (1, "Mittens", "beng", 3, 10, False)

    # Call the function and check the result
    result = get_cat_by_name("Mittens")

    # Expected result based on the simulated fetchone return value
    expected_result = Cat(1, "Mittens", "beng", 3, 10)

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, name, breed, age, weight, deleted FROM cats WHERE cat = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Mittens",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_cat_by_id_bad_name(mock_cursor):
    # Simulate that no cat exists for the given name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the cat is not found
    with pytest.raises(ValueError, match="Cat with name fluffy not found"):
        get_cat_by_name("fluffy")

def test_get_cat_by_deleted_name(mock_cursor):
    # Simulate that the cat has been deleted
    mock_cursor.fetchone.return_value = (1,"Mittens","beng",3,10,True)

    # Expect a ValueError when the cat is not found
    with pytest.raises(ValueError, match="Cat with name Mittens has been deleted"):
        get_cat_by_name("Mittens")

def test_get_cat_info(mocker):
    """Test fetching cat information using get_cat_info()."""

    # Mock the external API call to cat_info()
    mock_info = mocker.patch(
        "cat_curious.models.cat_model.cat_info", return_value="example info"
    )

    # Call the function being tested
    result = get_cat_info("drex")

    # Expected result based on the mock return value
    expected_result = "example info"

    # Assertions
    assert result == expected_result, f"Expected {expected_result}, got {result}"
    mock_info.assert_called_once_with("drex")

def test_get_cat_info_invalid_breed(mock_cursor):
    """Test error when trying to fetch cat information for an invalid breed."""

    # Simulate that no valid breed exists
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the breed is invalid or not found
    with pytest.raises(ValueError, match="Cat breed 'unknown_breed' not found"):
        get_cat_info("unknown_breed")

def test_get_cat_affection_level_invalid_breed(mock_cursor):
    """Test error when trying to fetch affection level for an invalid breed."""

    # Simulate that no cat exists with the given breed
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the breed is invalid
    with pytest.raises(ValueError, match="Cat breed 'unknown_breed' not found"):
        get_cat_affection("unknown_breed")

