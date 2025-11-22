from flask import Flask, request, jsonify
import requests
from crewai import Agent, Task

app = Flask(__name__)

# Replace with your n8n webhook URL
N8N_WEBHOOK_URL = "https://your-n8n-domain.com/webhook/upload_syllabus"

# Define an agent responsible for sending the PDF to n8n
n8n_agent = Agent(
    role="n8n Connector",
    goal="Send uploaded files to the n8n webhook backend",
    tools=["requests"]
)

@app.route('/upload', methods=['POST'])
def upload_syllabus():
    # Receive file from frontend
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    files = {'file': (file.filename, file.stream, file.mimetype)}

    # Define task for the CrewAI agent
    task = Task(
        description="Send the received PDF syllabus to the backend webhook.",
        agent=n8n_agent
    )

    # Agent sends file to n8n webhook
    response = requests.post(N8N_WEBHOOK_URL, files=files)

    if response.status_code == 200:
        return jsonify({"status": "success", "n8n_response": response.json()})
    else:
        return jsonify({"status": "error", "details": response.text}), 500


if __name__ == '__main__':
    app.run(port=5001, debug=True)

