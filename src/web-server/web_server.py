from flask import Flask, request, jsonify
import requests
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

APP_SERVER_URL = os.getenv("APP_SERVER_URL", "http://localhost:8000")

app = Flask(__name__)

class WebServer:
    def __init__(self):
        self.app_server_url = APP_SERVER_URL

    def validate_input(self, data):
        if not data or 'number' not in data:
            return False, "Missing 'number' field"

        try:
            number = int(data['number'])
        except (ValueError, TypeError):
            return False, "Number must be an integer"

        if number < 0:
            return False, "Number must be non-negative"

        return True, number

    def process_via_app_server(self, number):
        try:
            response = requests.post(
                f"{self.app_server_url}/process",
                json={"number": number},
                timeout=10
            )
            return response
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to application server")
            return None
        except requests.exceptions.Timeout:
            logger.error("Application server timeout")
            return None

web_server = WebServer()

@app.route('/process', methods=['POST'])
def process_number():
    try:
        data = request.get_json()

        is_valid, validation_result = web_server.validate_input(data)
        if not is_valid:
            logger.warning(f"Validation error: {validation_result}")
            return jsonify({"error": validation_result}), 400

        number = validation_result

        response = web_server.process_via_app_server(number)

        if response is None:
            return jsonify({"error": "Application server unavailable"}), 503

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            error_data = response.json()
            return jsonify(error_data), response.status_code

    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/numbers', methods=['GET'])
def get_numbers():
    try:
        response = requests.get(f"{web_server.app_server_url}/numbers", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Failed to get numbers"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Application server unavailable"}), 503

@app.route('/health', methods=['GET'])
def health_check():
    try:
        response = requests.get(f"{web_server.app_server_url}/health", timeout=5)
        app_server_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        app_server_status = "unreachable"

    return jsonify({
        "status": "healthy",
        "service": "web-server",
        "app_server": app_server_status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=False)
