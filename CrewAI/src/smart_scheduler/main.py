"""Main entry point for Smart Scheduler CrewAI application"""
from flask import Flask, request, jsonify
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.smart_scheduler.tools.n8n_tool import send_file_to_n8n

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

app = Flask(__name__)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://your-n8n-domain.com/webhook/upload_syllabus")

@app.route('/upload', methods=['POST'])
def upload_syllabus():
    """Handle syllabus file upload and process through CrewAI"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Get file details
        file_content = file.read()
        filename = file.filename
        mimetype = file.mimetype or 'application/pdf'
        
        # Use the n8n tool to send the file
        result = send_file_to_n8n(
            webhook_url=N8N_WEBHOOK_URL,
            file_content=file_content,
            filename=filename,
            mimetype=mimetype
        )
        
        if result.get("status") == "success":
            return jsonify({
                "status": "success",
                "n8n_response": result.get("response", {})
            }), 200
        else:
            return jsonify({
                "status": "error",
                "details": result.get("message", result.get("response", "Unknown error"))
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "details": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)

