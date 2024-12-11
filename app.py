from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from werkzeug.exceptions import BadRequest, Unauthorized

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

app = Flask(__name__)
db = SQLAlchemy()

def create_app(config_class=ProductionConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)  # Initialize db with app
    with app.app_context():
        db.create_all()  # Recreate all tables

    ####################################################
    #
    # Healthchecks
    #
    ####################################################

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """
        Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.
        """
        app.logger.info('Health check')
        return make_response(jsonify({'status': 'healthy'}), 200)


    @app.route('/api/db-check', methods=['GET'])
    def db_check() -> Response:
        """
        Route to check if the database connection and songs table are functional.

        Returns:
            JSON response indicating the database health status.
        Raises:
            404 error if there is an issue with the database.
        """
        try:
            app.logger.info("Checking database connection...")
            check_database_connection()
            app.logger.info("Database connection is OK.")
            app.logger.info("Checking if songs table exists...")
            check_table_exists("songs")
            app.logger.info("songs table exists.")
            return make_response(jsonify({'database_status': 'healthy'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 404)
    ##########################################################
    #
    # User management
    #
    ##########################################################
    
    @app.route('/api/create-account', methods=['POST'])
    def create_account() -> Response:
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

            # Call the User function to add the user to the database
            app.logger.info('Adding user: %s', username)
            Users.create_account(username, password)

            app.logger.info("User added: %s", username)
            return make_response(jsonify({'status': 'user added', 'username': username}), 201)
        except Exception as e:
            app.logger.error("Failed to add user: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)


    @app.route('/api/login', methods=['POST'])
    def login():
        """
        Route to log in a user and load their combatants.

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
            # Validate user credentials
            if not Users.check_password(username, password):
                app.logger.warning("Login failed for username: %s", username)
                raise Unauthorized("Invalid username or password.")

            app.logger.info("User %s logged in successfully.", username)
            return jsonify({"message": f"User {username} logged in successfully."}), 200

        except Unauthorized as e:
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            app.logger.error("Error during login for username %s: %s", username, str(e))
            return jsonify({"error": "An unexpected error occurred."}), 500

    @app.route('/api/update-password', methods=['PUT'])
    def update_password() -> Response:
        """
        Route to update the user's password.
        """
        data = request.get_json()
        username = data.get('username')
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not username or not old_password or not new_password:
            return make_response(jsonify({'error': 'All fields are required'}), 400)

        try:
            if not Users.check_password(username, old_password):
                return make_response(jsonify({'error': 'Incorrect old password'}), 401)

            Users.update_password(username, new_password)
            return make_response(jsonify({
                "message": f"Password updated successfully for user {username}."
            }), 200)

        except Exception as e:
            app.logger.error(f"Error updating password: {e}")
            return make_response(jsonify({'error': 'An unexpected error occurred.'}), 500)


    ##########################################################
    #
    # Cat Management
    #
    ##########################################################


    @app.route('/api/create-cat', methods=['POST'])
    def add_cat():
        """
        Add a new cat to the database.

        Expected JSON Input:
            - name (str): Cat's name.
            - breed (str): Cat's breed.
            - age (int): Cat's age.
            - weight (float): Cat's weight.

        Returns:
            JSON response with status and added cat details.
        """
        data = request.get_json()

        try:
            # Extract and validate input
            name = data['name']
            breed = data['breed']
            age = data['age']
            weight = data['weight']

            if not name or not breed or age <= 0 or weight <= 0:
                raise BadRequest("Invalid input. Ensure all fields are valid and positive.")

            # Add cat to the database
            Cat.create_cat(name, breed, age, weight)

            return jsonify({
                'status': 'success',
                'message': 'Cat added successfully.',
                'cat': {
                    'name': name,
                    'breed': breed,
                    'age': age,
                    'weight': weight
                }
            }), 201

        except BadRequest as e:
            app.logger.error(f"BadRequest: {str(e)}")
            return jsonify({'error': str(e)}), 400

        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred.'}), 500

            
    def clear_cats() -> Response:
        """
        Route to clear all cats from the database.

        Returns:
            JSON response indicating success of the operation or error message.
        """
        try:
            app.logger.info("Clearing all cats from the database")
            Cat.clear_cats()
            return make_response(jsonify({'status': 'success'}), 200)
        except Exception as e:
            app.logger.error(f"Error clearing catalog: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/delete-cat/<int:cat_id>', methods=['DELETE'])
    def delete_cat(cat_id: int) -> Response:
        """
        Route to delete a cat by its ID (soft delete).

        Path Parameter:
            - cat_id (int): The ID of the cat to delete.

        Returns:
            JSON response indicating success of the operation or error message.
        """
        try:
            app.logger.info(f"Deleting cat by ID: {cat_id}")
            Cat.delete_cat(cat_id)
            return make_response(jsonify({'status': 'success'}), 200)
        except Exception as e:
            app.logger.error(f"Error deleting song: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/get-cat-by-id/<int:cat_id>', methods=['GET'])
    def get_cat_by_id(cat_id: int) -> Response:
        """
        Route to retrieve a cat by its ID.

        Path Parameter:
            - cat_id (int): The ID of the cat.

        Returns:
            JSON response with the cat details or error message.
        """
        try:
            app.logger.info(f"Retrieving cat by ID: {cat_id}")
            cat = Cat.get_cat_by_id(cat_id)
            return make_response(jsonify({'status': 'success', 'cat': cat}), 200)
        except Exception as e:
            app.logger.error(f"Error retrieving cat by ID: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/get-cat-by-name/<string:cat_name>', methods=['GET'])
    def get_cat_by_name(cat_name: str) -> Response:
        """
        Route to retrieve a cat by its name.

        Path Parameter:
            - cat_name (str): The name of the cat.

        Returns:
            JSON response with the cat details or error message.
        """
        try:
            app.logger.info(f"Retrieving cat by name: {cat_name}")
            cat = Cat.get_cat_by_name(cat_name)
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
    def get_affection_level(breed: str) -> Response:
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
    def get_cat_facts(num_facts: int) -> Response:
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
    def get_cat_picture(breed: str) -> Response:
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
    def get_cat_lifespan(breed: str) -> Response:
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
    def get_random_cat_image() -> Response:
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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)



