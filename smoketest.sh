#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5001/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

##############################################
#
# User management
#
##############################################

create_account() {
  echo "Creating a new user..."
  response=$(curl -s -X POST "$BASE_URL/create-account" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "password":"password123"}')
  if echo "$response" | grep -q '"status": "user added"'; then
    echo "User created successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Create User Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to create user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Error Response JSON:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

# Function to log in a user
login() {
  echo "Logging in user..."
  response=$(curl -s -X POST "$BASE_URL/login" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "password":"password123"}')
  if echo "$response" | grep -q '"message": "User testuser logged in successfully."'; then
    echo "User logged in successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Login Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to log in user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Error Response JSON:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

# Function to update a user's password
update_password() {
  echo "Updating user password..."
  response=$(curl -s -X PUT "$BASE_URL/update-password" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "old_password":"password123", "new_password":"newpassword456"}')

  if echo "$response" | jq -e '.message == "Password updated successfully for user testuser."' >/dev/null; then
    echo "Password updated successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Update Password Response JSON:"
      echo "$response" | jq .
    fi
  else
    error_message=$(echo "$response" | jq -r '.error // "Unknown error occurred"')
    echo "Failed to update password: $error_message"
    if [ "$ECHO_JSON" = true ]; then
      echo "Error Response JSON:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

##############################################
#
# Cat
#
##############################################

create_cat() {
  echo "Adding a new cat..."
  response=$(curl -s -X POST "$BASE_URL/create-cat" -H "Content-Type: application/json" \
    -d '{"name":"Whiskers", "breed":"chau", "age":3, "weight":8}')

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat added successfully."
  else
    echo "Failed to add cat."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:" 
      echo "$response" | jq .
    fi
    exit 1
  fi
}

get_cat_by_id() {
  echo "Retrieving cat by ID..."
  response=$(curl -s -X GET "$BASE_URL/get-cat-by-id/2")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:" 
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve cat."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:" 
      echo "$response" | jq .
    fi
    exit 1
  fi
}

delete_cat_by_id() {
  echo "Deleting cat by ID..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-cat/2")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat deleted successfully."
  else
    echo "Failed to delete cat."
    if [ "$ECHO_JSON" = true ]; then
      echo "Response:" 
      echo "$response" | jq .
    fi
    exit 1
  fi
}
####################################################
#
# Cat Information
#
####################################################

# Function to get cat affection level
get_affection_level() {
  echo "Fetching affection level for Siamese..."
  response=$(curl -s -X GET "$BASE_URL/get-affection-level/Siamese")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Affection level fetched successfully."
    echo "$response" | jq .
  else
    echo "Failed to fetch affection level."
    echo "Error Response JSON:"
    echo "$response" | jq .
    exit 1
  fi
}

# Function to get random cat facts
get_cat_facts() {
  echo "Fetching 3 random cat facts..."
  response=$(curl -s -X GET "$BASE_URL/get-cat-facts/3")
  # Check if the response is valid JSON using jq
  if echo "$response" | jq empty 2>/dev/null; then
    # Check for a successful status in the response
    if echo "$response" | jq -e '.status == "success"' >/dev/null; then
      echo "Cat facts retrieved successfully."
      echo "$response" | jq .
    else
      echo "Failed to fetch cat facts."
      echo "Error Response JSON:"
      echo "$response" | jq .
      exit 1
    fi
  else
    echo "Error: Invalid JSON received from API."
    echo "Raw Response: $response"
    exit 1
  fi
}

# Function to get random cat image
get_random_cat_image() {
  echo "Fetching a random cat image..."
  response=$(curl -s -X GET "$BASE_URL/get-random-cat-image")
  if echo "$response" | jq empty 2>/dev/null; then
    if echo "$response" | jq -e '.status == "success"' >/dev/null; then
      echo "Random cat image fetched successfully."
      echo "$response" | jq .
    else
      echo "Failed to fetch random cat image."
      echo "Error Response JSON:"
      echo "$response" | jq .
      exit 1
    fi
  else
    echo "Error: Invalid JSON received from API."
    echo "Raw Response: $response"
    exit 1
  fi
}

# Function to get cat lifespan
get_cat_lifespan() {
  echo "Fetching lifespan for Siamese..."
  response=$(curl -s -X GET "$BASE_URL/get-cat-lifespan/Siamese")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat lifespan fetched successfully."
  else
    echo "Failed to fetch cat lifespan."
    exit 1
  fi
}

# Function to get a random cat image
get_random_cat_image() {
  echo "Fetching a random cat image..."
  response=$(curl -s -X GET "$BASE_URL/get-random-cat-image")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Random cat image fetched successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Random Cat Image Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to fetch random cat image."
    if [ "$ECHO_JSON" = true ]; then
      echo "Error Response JSON:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

# Function to initialize the database
init_db() {
  echo "Initializing the database..."
  response=$(curl -s -X POST "$BASE_URL/init-db")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Database initialized successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Initialization Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to initialize the database."
    exit 1
  fi
}

# Run all the steps in order
check_health
create_account
login
update_password
create_cat
get_cat_by_id
delete_cat_by_id
get_affection_level
get_cat_facts
get_random_cat_image

echo "All API tests passed successfully!"




