"""
API client for communicating with the Flask backend.
Provides wrapper functions around Flask endpoints.
"""
import requests
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# UPDATE THIS: Set BACKEND_URL environment variable to your Flask backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
# UPDATE THIS: Set N8N_WEBHOOK_URL environment variable to your n8n webhook URL for calendar integration
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


def upload_syllabus_to_n8n(
    file_path: str,
    user_id: str = "default_user",
    course_name: Optional[str] = None,
    course_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a syllabus PDF directly to n8n webhook for processing.
    
    n8n will process the PDF and upload dates to calendar.
    
    Args:
        file_path: Path to the PDF file
        user_id: User identifier
        course_name: Optional course name
        course_code: Optional course code
        
    Returns:
        Dictionary with success status and response data
    """
    if not N8N_WEBHOOK_URL:
        return {
            "success": False,
            "error": "N8N_WEBHOOK_URL not configured. Please set it in your .env file."
        }
    
    try:
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            data = {
                'user_id': user_id,
            }
            
            if course_name:
                data['course_name'] = course_name
            if course_code:
                data['course_code'] = course_code
            
            response = requests.post(
                N8N_WEBHOOK_URL,
                files=files,
                data=data,
                timeout=300  # n8n processing may take a while
            )
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json() if response.text else {}
                except:
                    response_data = {"message": response.text[:200] if response.text else "Success"}
                
                return {
                    "success": True,
                    "data": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def upload_syllabus_to_backend(
    file_path: str,
    user_id: str = "default_user",
    course_name: Optional[str] = None,
    course_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a syllabus PDF to the backend for processing.
    
    The backend will:
    1. Extract text from the PDF using PyPDF2
    2. Save the syllabus to the database
    3. Store it in the vector database for RAG (so CrewAI can access it)
    
    Args:
        file_path: Path to the PDF file
        user_id: User identifier
        course_name: Optional course name
        course_code: Optional course code
        
    Returns:
        Dictionary with success status and response data including syllabus_id
    """
    try:
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            data = {
                'user_id': user_id,
            }
            
            if course_name:
                data['course_name'] = course_name
            if course_code:
                data['course_code'] = course_code
            
            response = requests.post(
                f"{BACKEND_URL}/upload_syllabus",
                files=files,
                data=data,
                timeout=300  # PDF processing may take a while
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_plan(
    user_id: str,
    syllabus_id: Optional[int] = None,
    course_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a study plan via the backend.
    
    Args:
        user_id: User identifier
        syllabus_id: Optional syllabus ID
        course_name: Optional course name
        
    Returns:
        Dictionary with success status and plan data
    """
    try:
        payload = {
            "user_id": user_id
        }
        
        if syllabus_id:
            payload["syllabus_id"] = syllabus_id
        if course_name:
            payload["course_name"] = course_name
        
        response = requests.post(
            f"{BACKEND_URL}/generate_plan",
            json=payload,
            timeout=300  # Plan generation may take a while
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }




def health_check() -> Dict[str, Any]:
    """
    Check if the backend is healthy.
    
    Returns:
        Dictionary with health status
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
