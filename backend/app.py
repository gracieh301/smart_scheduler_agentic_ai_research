from flask import Flask, request, jsonify
import requests, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected"}), 400

    if not N8N_WEBHOOK_URL:
        return jsonify({"status": "error", "message": "N8N_WEBHOOK_URL not configured"}), 500

    try:
        # send to n8n webhook
        files = {"file": (file.filename, file.stream, file.mimetype)}
        response = requests.post(N8N_WEBHOOK_URL, files=files)
        
        # Check if n8n returned an error
        if response.status_code == 404:
            return jsonify({
                "status": "error",
                "message": "Webhook not found. Make sure your n8n workflow is active.",
                "n8n_response": response.text
            }), 404
        
        if response.status_code >= 400:
            return jsonify({
                "status": "error",
                "message": f"n8n returned error status {response.status_code}",
                "n8n_response": response.text
            }), response.status_code

        return jsonify({
            "status": "success",
            "n8n_response": response.text
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "error",
            "message": "Could not connect to n8n. Make sure n8n is running and the webhook URL is correct."
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
