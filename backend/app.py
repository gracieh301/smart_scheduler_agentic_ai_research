"""
Flask backend API for Study Plan Generator.
Provides REST endpoints for syllabus upload and study plan generation.
All logic runs in the backend - no logic in frontend.
"""
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import io

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Import backend modules
from db.models import init_db
from db.plan_ops import save_syllabus, get_study_plan, get_syllabus
from crew.crew import run_plan_generation

# PDF reading utility
try:
    from PyPDF2 import PdfReader
    PDF_READER_AVAILABLE = True
except ImportError:
    PDF_READER_AVAILABLE = False
    print("Warning: PyPDF2 not available. PDF upload will not work.")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize database on startup
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file content.
    
    Args:
        file_content: PDF file as bytes
    
    Returns:
        Extracted text as string
    """
    if not PDF_READER_AVAILABLE:
        raise ImportError("PyPDF2 package required for PDF processing")
    
    pdf = PdfReader(io.BytesIO(file_content))
    all_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            all_text += text + "\n"
    return all_text


@app.route("/upload_syllabus", methods=["POST"])
def upload_syllabus():
    """
    Upload and process a syllabus PDF.
    
    This endpoint:
    1. Receives a PDF file
    2. Extracts text from the PDF
    3. Saves the syllabus to the database
    
    Request:
        Form data with 'file' field (PDF file)
        Optional: 'user_id' field (defaults to 'default_user')
        Optional: 'course_name' field
        Optional: 'course_code' field
    
    Returns:
        JSON response with success status and syllabus_id
    """
    try:
        # Get file from request
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400
        
        file = request.files["file"]
        
        if file.filename == "":
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Get optional parameters
        user_id = request.form.get("user_id", "default_user")
        course_name = request.form.get("course_name", file.filename.replace(".pdf", "").replace("_", " "))
        course_code = request.form.get("course_code")
        
        # Read file content
        file_content = file.read()
        
        # Extract text from PDF
        try:
            extracted_text = extract_text_from_pdf(file_content)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                return jsonify({
                    "success": False,
                    "error": "Could not extract text from PDF. File may be corrupted or image-based."
                }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error extracting text from PDF: {str(e)}"
            }), 400
        
        # Save syllabus to database
        try:
            syllabus_id = save_syllabus(
                user_id=user_id,
                course_name=course_name,
                raw_text=extracted_text,
                file_name=file.filename,
                course_code=course_code
            )
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error saving syllabus to database: {str(e)}"
            }), 500
        
        return jsonify({
            "success": True,
            "syllabus_id": syllabus_id,
            "message": f"Syllabus uploaded and stored successfully",
            "course_name": course_name,
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/generate_plan", methods=["POST"])
def generate_plan():
    """
    Generate a study plan using CrewAI.
    
    This endpoint:
    1. Receives user_id and optional syllabus_id
    2. Calls the CrewAI supervisor to generate a study plan
    3. Returns the generated plan
    
    Request body:
        {
            "user_id": "user123" (required),
            "syllabus_id": 123 (optional),
            "course_name": "Machine Learning" (optional)
        }
    
    Returns:
        JSON response with success status and plan data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        user_id = data.get("user_id")
        syllabus_id = data.get("syllabus_id")
        course_name = data.get("course_name")
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing 'user_id' field"
            }), 400
        
        # Run CrewAI to generate plan
        result = run_plan_generation(
            user_id=user_id,
            syllabus_id=syllabus_id,
            course_name=course_name
        )
        
        if result.get("success"):
            # Get the saved plan from database
            plan = get_study_plan(user_id=user_id)
            
            return jsonify({
                "success": True,
                "message": "Study plan generated successfully",
                "plan": plan,
                "crew_result": result.get("result")
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Unknown error during plan generation")
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/syllabus/<int:syllabus_id>", methods=["GET"])
def get_syllabus_endpoint(syllabus_id: int):
    """
    Get syllabus data by ID.
    
    This endpoint allows n8n or other services to fetch full syllabus data
    including raw_text and structured_data for processing.
    
    Args:
        syllabus_id: ID of the syllabus to retrieve
    
    Returns:
        JSON response with syllabus data
    """
    try:
        syllabus = get_syllabus(syllabus_id)
        
        if not syllabus:
            return jsonify({
                "success": False,
                "error": f"Syllabus with ID {syllabus_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": syllabus
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with status information
    """
    return jsonify({
        "status": "healthy",
        "pdf_reader_available": PDF_READER_AVAILABLE
    }), 200


if __name__ == "__main__":
    # Run the Flask app
    # UPDATE THIS: Set FLASK_PORT environment variable to change port (default: 5000)
    port = int(os.getenv("FLASK_PORT", 5000))
    # UPDATE THIS: Set FLASK_DEBUG environment variable to "true" for debug mode
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    print(f"Starting Study Plan Generator backend on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(port=port, debug=debug)
