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
from db.plan_ops import save_syllabus, get_study_plan
from vector.rag import load_and_embed_syllabus
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
    4. Stores it in the vector database for RAG
    
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
        
        # Store in vector database for RAG
        # This can take a while for large PDFs, so we do it after saving to DB
        try:
            print(f"Starting vector DB embedding generation for syllabus {syllabus_id}...")
            print(f"Text length: {len(extracted_text)} characters")
            load_and_embed_syllabus(
                syllabus_text=extracted_text,
                user_id=user_id,
                course_name=course_name,
                syllabus_id=syllabus_id
            )
            print(f"Successfully stored syllabus {syllabus_id} in vector DB")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Warning: Failed to store syllabus in vector DB: {e}")
            print(f"Full traceback:\n{error_trace}")
            # Continue even if vector DB storage fails - syllabus is already saved to DB
        
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


@app.route("/store_syllabus_from_n8n", methods=["POST"])
def store_syllabus_from_n8n():
    """
    Store syllabus information received from N8N.
    
    This endpoint receives the processed syllabus data from N8N and stores it
    in the database. N8N should send a JSON object with syllabus information
    after processing the PDF.
    
    Expected JSON structure from N8N:
    {
        "Course Name": "Machine Learning",
        "Course Code": "CS101",
        "Class Times": ["Monday 10:00 AM", "Wednesday 2:00 PM"],
        "Lab Due Dates": ["2024-01-15", "2024-02-20"],
        "Midterm Date": "2024-03-10"
    }
    
    The request should also include user_id and file_name in the JSON
    or as form data (sent from Streamlit).
    
    Returns:
        JSON response with success status and syllabus_id
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Extract user_id from data or form (Streamlit sends it)
        user_id = data.get("user_id") or request.form.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing 'user_id' field. Please include it in the JSON or form data."
            }), 400
        
        # Extract course name from N8N's "Course Name" field
        course_name = data.get("Course Name", "").strip()
        if not course_name:
            return jsonify({
                "success": False,
                "error": "Missing 'Course Name' field in N8N response"
            }), 400
        
        # Get optional fields
        course_code = data.get("Course Code", "").strip() or request.form.get("course_code")
        file_name = data.get("file_name") or request.form.get("file_name")
        
        # Extract structured data from N8N (preserve original format)
        structured_data = {
            "Course Name": data.get("Course Name"),
            "Course Code": data.get("Course Code", ""),
            "Class Times": data.get("Class Times", []),
            "Lab Due Dates": data.get("Lab Due Dates", []),
            "Midterm Date": data.get("Midterm Date", "")
        }
        
        # Create raw_text from structured data for RAG purposes
        # This allows CrewAI agents to search the syllabus content
        raw_text_parts = [
            f"Course Name: {course_name}",
        ]
        
        if course_code:
            raw_text_parts.append(f"Course Code: {course_code}")
        
        if structured_data.get("Class Times"):
            raw_text_parts.append(f"Class Times: {', '.join(structured_data['Class Times'])}")
        
        if structured_data.get("Lab Due Dates"):
            raw_text_parts.append(f"Lab Due Dates: {', '.join(structured_data['Lab Due Dates'])}")
        
        if structured_data.get("Midterm Date"):
            raw_text_parts.append(f"Midterm Date: {structured_data['Midterm Date']}")
        
        raw_text = "\n".join(raw_text_parts)
        
        # Save to database
        try:
            syllabus_id = save_syllabus(
                user_id=user_id,
                course_name=course_name,
                raw_text=raw_text,
                file_name=file_name,
                course_code=course_code,
                structured_data=structured_data
            )
            
            return jsonify({
                "success": True,
                "syllabus_id": syllabus_id,
                "message": "Syllabus stored successfully from N8N",
                "course_name": course_name,
                "user_id": user_id,
                "structured_data": structured_data
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error saving syllabus to database: {str(e)}"
            }), 500
        
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
