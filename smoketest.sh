#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

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

# Function to create a user
create_account() {
  echo "Creating a new user..."
  curl -s -X POST "$BASE_URL/create-account" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "password":"password123"}' | grep -q '"status": "user added"'
  if [ $? -eq 0 ]; then
    echo "Account created successfully."
  else
    echo "Failed to create user."
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
  response=$(curl -s -X PUT "$BASE_URL/api/update-password" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "old_password":"password123", "new_password":"newpassword456"}')
  if echo "$response" | grep -q '"message": "Password updated successfully for user testuser."'; then
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

# Function to add a cat
create_cat() {
  echo "Adding a cat..."
  curl -s -X POST "$BASE_URL/api/create-cat" -H "Content-Type: application/json" \
    -d '{"name":"Whiskers", "breed":"Siamese", "age":3, "weight":8}' | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Cat added successfully."
  else
    echo "Failed to add cat."
    exit 1
  fi
}

# Function to clear all cats
clear_cats() {
  echo "Clearing cats..."
  response=$(curl -s -X DELETE "$BASE_URL/api/clear-cats")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cats cleared successfully."
  else
    echo "Failed to clear cats."
    exit 1
  fi
}

# Function to delete a cat by ID (1)
delete_cat_by_id() {
  echo "Deleting cat by ID (1)..."
  response=$(curl -s -X DELETE "$BASE_URL/api/delete-cat/1")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat deleted successfully by ID (1)."
  else
    echo "Failed to delete cat by ID (1)."
    exit 1
  fi
}

# Function to get a cat by ID (1)
get_cat_by_id() {
  echo "Getting cat by ID (1)..."
  response=$(curl -s -X GET "$BASE_URL/get-cat-by-id/1")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat retrieved successfully by ID (1)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Cat JSON (ID 1):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get cat by ID (1)."
    exit 1
  fi
}

# Function to get a cat by name
get_cat_by_name() {
  echo "Getting cat by name (Fluffy)..."
  response=$(curl -s -X GET "$BASE_URL/get-cat-by-name/Fluffy")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat retrieved successfully by name (Fluffy)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Cat JSON (Fluffy):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name (Spaghetti)."
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
  else
    echo "Failed to fetch affection level."
    exit 1
  fi
}

# Function to get random cat facts
get_cat_facts() {
  echo "Fetching 3 random cat facts..."
  response=$(curl -s -X GET "$BASE_URL/get-cat-facts/3")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Cat facts retrieved successfully."
  else
    echo "Failed to fetch cat facts."
    exit 1
  fi
}

# Function to get random cat image
get_random_cat_image() {
  echo "Fetching a random cat image..."
  response=$(curl -s -X GET "$BASE_URL/get-random-cat-image")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Random cat image fetched successfully."
  else
    echo "Failed to fetch random cat image."
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
db_check
init_db
create_account
login
update_password
create_cat
get_cat_by_id
get_cat_by_name
delete_cat_by_id
clear_cats
get_affection_level
get_cat_facts
get_random_cat_image
get_cat_lifespan

echo "All API tests passed successfully!"




