from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from werkzeug.exceptions import BadRequest, Unauthorized
import requests 
import os

from config import ProductionConfig
from cat_curious.db import *
from cat_curious.models.user_model import Users

from cat_curious.models.cat_model import Cat
from cat_curious.utils.sql_utils import check_database_connection, check_table_exists
from cat_curious.utils.cat_affection_utils import get_affection_level
from cat_curious.utils.cat_facts_utils import get_random_cat_facts
from cat_curious.utils.cat_random_image_utils import get_random_cat_image
from cat_curious.utils.cat_info_utils import cat_info
from cat_curious.utils.cat_lifespan_utils import get_cat_lifespan
from sqlalchemy.exc import IntegrityError


# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("KEY")

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
    def create_cat():
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
            name = data['name']
            breed = data['breed']
            age = data['age']
            weight = data['weight']

            if not name or not breed or age <= 0 or weight <= 0:
                return jsonify({'error': 'Invalid input. Ensure all fields are valid and positive.'}), 400

            Cat.create_cat(name, breed, age, weight)
            return jsonify({'status': 'success', 'message': 'Cat added successfully.'}), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': f"Cat with name '{name}' already exists."}), 409
        except Exception as e:
            app.logger.error(f"Error creating cat: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/delete-cat/<int:cat_id>', methods=['DELETE'])
    def delete_cat(cat_id):
        """Delete a cat by its ID."""
        try:
            Cat.delete_cat(cat_id)
            return jsonify({'status': 'success', 'message': f'Cat with ID {cat_id} deleted successfully.'}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            app.logger.error(f"Error deleting cat: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/get-cat-by-id/<int:cat_id>', methods=['GET'])
    def get_cat_by_id(cat_id):
        """Retrieve a cat by its unique ID."""
        try:
            cat = Cat.get_cat_by_id(cat_id)
            return jsonify({'status': 'success', 'cat': cat.to_dict()}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            app.logger.error(f"Error retrieving cat: {e}")
            return jsonify({'error': str(e)}), 500

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
            url = f"https://api.thecatapi.com/v1/breeds/search?q={breed}&api_key={API_KEY}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data:
                affection_level = data[0].get("affection_level")
                if affection_level is not None:
                    app.logger.info(f"Received affection level: {affection_level}")
                    return make_response(jsonify({
                        'status': 'success', 
                        'breed': breed, 
                        'affection_level': affection_level
                    }), 200)
                else:
                    app.logger.error("Affection level not found.")
                    return make_response(jsonify({'error': 'Affection level not found.'}), 404)
            else:
                app.logger.error("No breed information received from API.")
                return make_response(jsonify({'error': 'No breed information received from API.'}), 500)

        except requests.exceptions.Timeout:
            app.logger.error("Request to TheCatAPI timed out.")
            return make_response(jsonify({'error': 'Request to TheCatAPI timed out.'}), 504)
        except requests.exceptions.RequestException as e:
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
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "data" not in data:
                app.logger.error("Invalid response from Cat Facts API: %s", data)
                return make_response(jsonify({'error': 'Invalid response from Cat Facts API.'}), 500)

            facts = [fact["fact"] for fact in data["data"]]

            app.logger.info("Fetched %d cat facts.", len(facts))
            return make_response(jsonify({'status': 'success', 'facts': facts}), 200)
        
        except ValueError as ve:
            app.logger.error("Invalid request to Cat Facts API: %s", ve)
            return make_response(jsonify({'error': str(ve)}), 400)

        except requests.exceptions.Timeout:
            app.logger.error("Request to Cat Facts API timed out.")
            return make_response(jsonify({'error': 'Request to Cat Facts API timed out.'}), 504)

        except requests.exceptions.RequestException as e:
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
        url = f"https://api.thecatapi.com/v1/images/search?limit=1&breed_ids={breed}&api_key={API_KEY}"
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
        """
        try:
            lifespan, api_data = get_cat_lifespan(breed)
            
            app.logger.info("Successfully retrieved lifespan for breed '%s': %s years", breed, lifespan)
            app.logger.info("Full API Response: %s", api_data)

            # Return success response
            return jsonify({
                'status': 'success',
                'breed': breed,
                'lifespan': lifespan,
                'api_data': api_data
            }), 200

        except RuntimeError as re:
            app.logger.error("RuntimeError fetching cat lifespan for breed '%s': %s", breed, re)
            return jsonify({'error': str(re)}), 502

        except Exception as e:
            app.logger.error("Unexpected error fetching cat lifespan for breed '%s': %s", breed, e, exc_info=True)
            return jsonify({'error': f'Unexpected error: {e}'}), 500


    @app.route('/api/get-random-cat-image', methods=['GET'])
    def get_random_cat_imagee() -> Response:
        """
        Route to fetch a random cat image from TheCatAPI.
        """
        try:
            cat_image_url = get_random_cat_image()  # Ensure this returns a plain string

            return jsonify({
                'status': 'success',
                'cat_image_url': cat_image_url
            })

        except RuntimeError as re:
            app.logger.error("RuntimeError fetching random cat image: %s", re)
            return jsonify({'error': str(re)}), 502

        except Exception as e:
            app.logger.error("Unexpected error fetching random cat image: %s", e, exc_info=True)
            return jsonify({'error': f'Unexpected error: {e}'}), 500


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)



