from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from werkzeug.exceptions import BadRequest, Unauthorized
import os
from config import ProductionConfig
from cat_curious.db import *
from cat_curious.models.user_model import Users

from cat_curious.models.cat_model import Cat
from cat_curious.utils.sql_utils import check_database_connection, check_table_exists
from cat_curious.utils.cat_affection_utils import get_affection_level
from cat_curious.utils.cat_facts_utils import get_random_cat_facts
from cat_curious.utils.cat_info_utils import cat_info

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')  # Replace with your DB URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)
cat_model = Cat(id=-1, name="Whiskers", breed="beng", age=3, weight=8)

""" # Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing primary key
    username = db.Column(db.String(50), unique=True, nullable=False)  # User's username
    password_hash = db.Column(db.String(128), nullable=False)  # Hashed password

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = Users.generate_password_hash(password)

    def check_password(self, password):
        return Users.check_password_hash(self.password_hash, password)

# Define the Cat model
class Cat(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing primary key
    name = db.Column(db.String(50), nullable=False)  # Cat's name
    breed = db.Column(db.String(50), nullable=False)  # Cat's breed
    age = db.Column(db.Integer, nullable=False)  # Cat's age
    weight = db.Column(db.Float, nullable=False)  # Cat's weight

    def __repr__(self):
        return f'<Cat {self.name}>' """

# Create the database tables
with app.app_context():
    db.create_all()

####################################################
#
# Healthchecks
#
####################################################

@app.route('/api/health', methods=['GET'])
def healthcheck():
    """
    Health check route to verify the service is running.

    Returns:
        JSON response indicating the health status of the service.
    """
    app.logger.info('Health check')
    return make_response(jsonify({'status': 'healthy'}), 200)

##########################################################
#
# User management
#
##########################################################

@app.route('/api/create-account', methods=['POST'])
def create_account():
    """
    Route to create a new user.

    Expected JSON Input:
        - username (str): The username for the new user.
        - password (str): The password for the new user.

    Returns:
        JSON response indicating the success of user creation.
    Raises:
        400 error if input validation fails.
        500 error if there is an issue adding the user to the database.
    """
    app.logger.info('Creating new user')
    try:
        # Get the JSON data from the request
        data = request.get_json()

        # Extract and validate required fields
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return make_response(jsonify({'error': 'Invalid input, both username and password are required'}), 400)

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            return make_response(jsonify({'error': 'Username already exists'}), 400)

        # Create a new user instance
        new_user = User(username=username)
        new_user.set_password(password)

        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        app.logger.info("User added: %s", username)
        return make_response(jsonify({'status': 'user added', 'username': username}), 201)
    except Exception as e:
        app.logger.error("Failed to add user: %s", str(e))
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/login', methods=['POST'])
def login():
    """
    Route to log in a user.

    Expected JSON Input:
        - username (str): The username of the user.
        - password (str): The user's password.

    Returns:
        JSON response indicating the success of the login.
    
    Raises:
        400 error if input validation fails.
        401 error if authentication fails (invalid username or password).
        500 error for any unexpected server-side issues.
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        app.logger.error("Invalid request payload for login.")
        raise BadRequest("Invalid request payload. 'username' and 'password' are required.")

    username = data['username']
    password = data['password']

    try:
        # Retrieve user from the database
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            app.logger.warning("Login failed for username: %s", username)
            raise Unauthorized("Invalid username or password.")

        app.logger.info("User logged in: %s", username)
        return jsonify({"message": "Login successful."}), 200
    except Unauthorized as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        app.logger.error("Error during login for username %s: %s", username, str(e))
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route('/api/update-password', methods=['PUT'])
def update_password():
    """
    Route to update the password of the user. 

    Expected JSON Input:
        - username (str): The user's username. 
        - old_password (str): The user's current password. 
        - new_password (str): The new password for the user.

    Returns:
        JSON response indicating the success of the password update.
        Raises:
            400 error if input validation fails.
            401 error if old password is incorrect.
            500 error if there is an issue with updating the password.
    """
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not username or not old_password or not new_password:
        raise BadRequest("Username, old_password, and new_password fields are all required.")

    try:
        # Retrieve user from the database
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(old_password):
            raise Unauthorized("Incorrect old password.")

        # Update the password
        user.set_password(new_password)
        db.session.commit()

        app.logger.info("Password updated successfully for user %s.", username)
        return jsonify({"message": f"Password updated successfully for user {username}."}), 200

    except Unauthorized as e:
        app.logger.warning("Password update failed for %s: %s", username, str(e))
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        app.logger.error("Error while updating password: %s", str(e))
        return jsonify({"error": "An unexpected error occured."}), 500
 

##########################################################
#
# Cat Management
#
##########################################################

@app.route('/api/create-cat', methods=['POST'])
def add_cat():
    app.logger.info('Adding a new cat to the database')
    try:
        data = request.get_json()

        name = data.get('name')
        breed = data.get('breed')
        age = data.get('age')
        weight = data.get('weight')

        if not name or not breed or age is None or weight is None:
            return make_response(jsonify({'error': 'Invalid input, all fields are required with valid values'}), 400)

        new_cat = Cat(name=name, breed=breed, age=age, weight=weight)
        db.session.add(new_cat)
        db.session.commit()

        app.logger.info("Cat added to the database: %s", name)
        return make_response(jsonify({'status': 'success', 'cat': name}), 201)
    except Exception as e:
        app.logger.error("Failed to add cat: %s", str(e))
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/clear-cats', methods=['DELETE'])
def clear_cats():
    try:
        app.logger.info("Clearing all cats from the database")
        num_rows_deleted = db.session.query(Cat).delete()
        db.session.commit()
        app.logger.info("Deleted %d cats from the database", num_rows_deleted)
        return make_response(jsonify({'status': 'success', 'deleted': num_rows_deleted}), 200)
    except Exception as e:
        app.logger.error(f"Error clearing cats: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@app.route('/api/delete-cat/<int:cat_id>', methods=['DELETE'])
def delete_cat(cat_id: int):
    """
    Route to delete a cat by its ID (soft delete).

    Path Parameter:
        - cat_id (int): The ID of the cat to delete.

    Returns:
        JSON response indicating success of the operation or error message.
    """
    try:
        app.logger.info(f"Deleting cat by ID: {cat_id}")
        cat_model.delete_cat(cat_id)
        return make_response(jsonify({'status': 'success'}), 200)
    except Exception as e:
        app.logger.error(f"Error deleting song: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-by-id/<int:cat_id>', methods=['GET'])
def get_cat_by_id(cat_id: int):
    """
    Route to retrieve a cat by its ID.

    Path Parameter:
        - cat_id (int): The ID of the cat.

    Returns:
        JSON response with the cat details or error message.
    """
    try:
        app.logger.info(f"Retrieving cat by ID: {cat_id}")
        cat = cat_model.get_cat_by_id(cat_id)
        return make_response(jsonify({'status': 'success', 'cat': cat}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving cat by ID: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-by-name/<string:cat_name>', methods=['GET'])
def get_cat_by_name(cat_name: str):
    """
    Route to retrieve a cat by its name.

    Path Parameter:
        - cat_name (str): The name of the cat.

    Returns:
        JSON response with the cat details or error message.
    """
    try:
        app.logger.info(f"Retrieving cat by name: {cat_name}")
        cat = cat_model.get_cat_by_name(cat_name)
        return make_response(jsonify({'status': 'success', 'cat': cat}), 200)
    except Exception as e:
        app.logger.error(f"Error retrieving cat by name: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/init-db', methods=['POST'])
def init_db():
    """
    Initialize or recreate database tables.

    This route initializes the database tables defined in the SQLAlchemy models.
    If the tables already exist, they are dropped and recreated to ensure a clean
    slate. Use this with caution as all existing data will be deleted.

    Returns:
        Response: A JSON response indicating the success or failure of the operation.

    Logs:
        Logs the status of the database initialization process.
    """
    try:
        with app.app_context():
            app.logger.info("Dropping all existing tables.")
            db.drop_all()  # Drop all existing tables
            app.logger.info("Creating all tables from models.")
            db.create_all()  # Recreate all tables
        app.logger.info("Database initialized successfully.")
        return jsonify({"status": "success", "message": "Database initialized successfully."}), 200
    except Exception as e:
        app.logger.error("Failed to initialize database: %s", str(e))
        return jsonify({"status": "error", "message": "Failed to initialize database."}), 500

####################################################
#
# Cat Information
#
####################################################

@app.route('/api/get-affection-level/<string:breed>', methods=['GET'])
def get_affection_level(breed: str):
    """
    Route to fetch the affection level of a cat breed using TheCatAPI.

    Path Parameter:
        - breed (str): The cat breed to get affection level for.

    Returns:
        JSON response indicating the affection level or error message.
    """
    try:
        app.logger.info(f"Fetching affection level for breed: {breed}")
        url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
        response = request.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data and "breeds" in data[0]:
            affection_level = data[0]["breeds"][0]["affection_level"]
            app.logger.info(f"Received affection level: {affection_level}")
            return make_response(jsonify({'status': 'success', 'breed': breed, 'affection_level': affection_level}), 200)
        else:
            app.logger.error("No breed information received from API.")
            return make_response(jsonify({'error': 'No breed information received from API.'}), 500)

    except request.exceptions.Timeout:
        app.logger.error("Request to TheCatAPI timed out.")
        return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)
    except request.exceptions.RequestException as e:
        app.logger.error(f"Request to TheCatAPI failed: {e}")
        return make_response(jsonify({'error': f'Request failed: {e}'}), 502)
    except Exception as e:
        app.logger.error(f"Error retrieving affection level of cat: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-facts/<int:num_facts>', methods=['GET'])
def get_cat_facts(num_facts: int):
    """
    Route to fetch a certain number of random cat facts.

    Path Parameter:
        - num_facts (int): The number of cat facts to retrieve.

    Returns:
        JSON response with the list of cat facts or error message.
    """
    if num_facts <= 0:
        app.logger.error("Invalid number of cat facts requested: %d", num_facts)
        return make_response(jsonify({'error': 'Num_facts must be a positive integer.'}), 400)

    url = f"https://catfact.ninja/facts?limit={num_facts}"
    try:
        app.logger.info("Fetching %d random cat facts from %s", num_facts, url)
        response = request.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "data" not in data:
            app.logger.error("Invalid response from Cat Facts API: %s", data)
            return make_response(jsonify({'error': 'Invalid response from Cat Facts API.'}), 500)

        facts = [fact["fact"] for fact in data["data"]]

        app.logger.info("Fetched %d cat facts.", len(facts))
        return make_response(jsonify({'status': 'success', 'facts': facts}), 200)

    except request.exceptions.Timeout:
        app.logger.error("Request to Cat Facts API timed out.")
        return make_response(jsonify({'error': 'Request to Cat Facts API timed out.'}), 504)

    except request.exceptions.RequestException as e:
        app.logger.error("Request to Cat Facts API failed: %s", e)
        return make_response(jsonify({'error': f'Request to Cat Facts API failed: {e}'}), 502)

    except Exception as e:
        app.logger.error("Error retrieving random number of cat facts: %s", e)
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-pic/<string:breed>', methods=['GET'])
def get_cat_picture(breed: str):
    """
    Route to fetch a cat picture for a cat breed.

    Path Parameter:
        - breed (str): The cat's breed name.

    Returns:
        JSON response with the URL of cat picture or error message.
    """
    url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={KEY}"
    try:
        app.logger.info(f"Fetching cat picture for breed: {breed} from {url}")
        response = request.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "url" in data[0]:
            cat_pic_url = data[0]["url"]
            app.logger.info(f"Fetched cat picture URL: {cat_pic_url}")
            return make_response(jsonify({'status': 'success', 'cat_picture_url': cat_pic_url}), 200)
        else:
            app.logger.error("Data received from TheCatAPI not received.")
            return make_response(jsonify({'error': 'Data received from TheCatAPI not received.'}), 500)

    except request.exceptions.Timeout:
        app.logger.error("Request to TheCatAPI timed out.")
        return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)

    except request.exceptions.RequestException as e:
        app.logger.error(f"Request to TheCatAPI failed: {e}")
        return make_response(jsonify({'error': f'Request to TheCatAPI failed: {e}'}), 502)

    except Exception as e:
        app.logger.error(f"Error retrieving cat picture: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-cat-lifespan/<string:breed>', methods=['GET'])
def get_cat_lifespan(breed: str):
    """
    Route to fetch the lifespan of a cat breed using TheCatAPI.

    Path Parameter:
        - breed (str): The cat breed to get lifespan for.

    Returns:
        JSON response indicating the lifespan or error message.
    """
    try:
        app.logger.info(f"Fetching lifespan for breed: {breed}")
        url = f"https://api.thecatapi.com/v1/breeds?breed_ids={breed}&api_key={KEY}"
        response = request.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data:
            lifespan = data[0].get("life_span")
            app.logger.info(f"Received lifespan: {lifespan}")
            return make_response(jsonify({'status': 'success', 'breed': breed, 'lifespan': lifespan}), 200)
        else:
            app.logger.error("No breed information received from API.")
            return make_response(jsonify({'error': 'No breed information received from API.'}), 500)

    except request.exceptions.Timeout:
        app.logger.error("Request to TheCatAPI timed out.")
        return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)
    except request.exceptions.RequestException as e:
        app.logger.error(f"Request to TheCatAPI failed: {e}")
        return make_response(jsonify({'error': f'Request failed: {e}'}), 502)
    except Exception as e:
        app.logger.error(f"Error retrieving lifespan for breed {breed}: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/api/get-random-cat-image', methods=['GET'])
def get_random_cat_image():
    """
    Route to fetch a random cat image from TheCatAPI.

    Returns:
        JSON response with the URL of the random cat image or an error message.
    """
    url = "https://api.thecatapi.com/v1/images/search?limit=1&api_key={KEY}"
    try:
        app.logger.info(f"Fetching random cat image from {url}")
        response = request.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data and "url" in data[0]:
            cat_image_url = data[0]["url"]
            app.logger.info(f"Fetched random cat image URL: {cat_image_url}")
            return make_response(jsonify({'status': 'success', 'cat_image_url': cat_image_url}), 200)
        else:
            app.logger.error("Data received from TheCatAPI not received.")
            return make_response(jsonify({'error': 'Data received from TheCatAPI not received.'}), 500)

    except request.exceptions.Timeout:
        app.logger.error("Request to TheCatAPI timed out.")
        return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)

    except request.exceptions.RequestException as e:
        app.logger.error(f"Request to TheCatAPI failed: {e}")
        return make_response(jsonify({'error': f'Request to TheCatAPI failed: {e}'}), 502)

    except Exception as e:
        app.logger.error(f"Error retrieving random cat image: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)