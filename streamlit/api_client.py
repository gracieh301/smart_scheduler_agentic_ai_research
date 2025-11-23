"""
API client for communicating with the Flask backend.
Provides wrapper functions around Flask endpoints.
"""
import requests
from typing import Optional, Dict, Any
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

# UPDATE THIS: Set BACKEND_URL environment variable to your Flask backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
# UPDATE THIS: Set N8N_WEBHOOK_URL environment variable to your n8n webhook URL for syllabus uploads
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


def store_syllabus_from_n8n(n8n_response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store syllabus information received from N8N into the database.
    
    This function takes the JSON response from N8N and stores it in the
    Flask backend database for use in study plan generation.
    
    Args:
        n8n_response_data: JSON object from N8N with syllabus information
                          Expected fields: user_id, course_name, raw_text,
                          and optionally: course_code, file_name, syllabus_id
        
    Returns:
        Dictionary with success status and stored syllabus data
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/store_syllabus_from_n8n",
            json=n8n_response_data,
            timeout=30
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


def upload_syllabus_to_n8n(
    file_path: str,
    user_id: str = "default_user",
    course_name: Optional[str] = None,
    course_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a syllabus PDF directly to N8N webhook and store the response.
    
    This function:
    1. Sends the PDF file to N8N webhook
    2. Receives processed syllabus data (JSON) from N8N
    3. Stores the syllabus information in the database via Flask backend
    
    Args:
        file_path: Path to the PDF file
        user_id: User identifier
        course_name: Optional course name
        course_code: Optional course code
        
    Returns:
        Dictionary with success status and response data including syllabus_id
    """
    if not N8N_WEBHOOK_URL:
        return {
            "success": False,
            "error": "N8N_WEBHOOK_URL not configured. Please set it in your .env file."
        }
    
    try:
        # Step 1: Upload PDF to N8N
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
            
            n8n_response = requests.post(
                N8N_WEBHOOK_URL,
                files=files,
                data=data,
                timeout=300  # N8N processing timeout
            )
            
            if n8n_response.status_code not in [200, 201]:
                return {
                    "success": False,
                    "error": f"N8N returned HTTP {n8n_response.status_code}: {n8n_response.text}"
                }
            
            # Step 2: Parse N8N's JSON response
            # N8N might return:
            # 1. Direct JSON object: {"Course Name": "..."}
            # 2. Array with output field (JSON object): [{"output": {"Course Name": "..."}}]
            # 3. Array with output field (markdown string): [{"output": "```json\n{...}\n```"}]
            # 4. String with markdown: "```json\n{...}\n```"
            n8n_data = None
            response_text = n8n_response.text
            
            # First try to parse as JSON directly
            try:
                parsed_response = n8n_response.json()
                
                # Check if it's an array with an "output" field
                if isinstance(parsed_response, list) and len(parsed_response) > 0:
                    first_item = parsed_response[0]
                    if isinstance(first_item, dict) and "output" in first_item:
                        output_value = first_item["output"]
                        
                        # Check if output is already a JSON object (dict)
                        if isinstance(output_value, dict):
                            # Output is already parsed JSON object - use it directly
                            n8n_data = output_value
                        elif isinstance(output_value, str):
                            # Output is a string (might be markdown) - extract JSON from it
                            response_text = output_value
                    elif isinstance(first_item, dict):
                        # If it's a dict but not with "output", use it directly
                        n8n_data = first_item
                elif isinstance(parsed_response, dict):
                    # If it's already a dict with the data we need, use it
                    if "Course Name" in parsed_response:
                        n8n_data = parsed_response
                    elif "output" in parsed_response:
                        output_value = parsed_response["output"]
                        if isinstance(output_value, dict):
                            # Output is already a JSON object
                            n8n_data = output_value
                        elif isinstance(output_value, str):
                            # Extract from output string
                            response_text = output_value
                        
            except (ValueError, json.JSONDecodeError):
                # Response is not JSON, treat as plain text
                pass
            
            # If we don't have the data yet, extract JSON from the text (markdown or plain)
            if n8n_data is None:
                # Try to find JSON in markdown code blocks (```json ... ```)
                json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response_text)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        n8n_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # If parsing fails, try to clean up the JSON string
                        json_str = json_match.group(1).strip()
                        try:
                            n8n_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            pass
                
                # If still no JSON, try to find any JSON object in the text
                if n8n_data is None:
                    # Find the first { and match until the last } (handles nested objects)
                    start_idx = response_text.find('{')
                    if start_idx != -1:
                        # Count braces to find matching closing brace
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response_text)):
                            if response_text[i] == '{':
                                brace_count += 1
                            elif response_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if end_idx > start_idx:
                            json_str = response_text[start_idx:end_idx]
                            try:
                                n8n_data = json.loads(json_str)
                            except json.JSONDecodeError:
                                pass
                
                # If we still don't have valid JSON, return error with helpful message
                if n8n_data is None:
                    return {
                        "success": False,
                        "error": f"N8N did not return valid JSON. Response preview: {response_text[:500]}\n\nTip: Make sure your N8N workflow returns JSON in the format: [{{\"output\": {{\"Course Name\": \"...\"}}}}] or direct JSON object."
                    }
            
            # Step 3: Validate N8N response structure
            if not n8n_data.get("Course Name"):
                return {
                    "success": False,
                    "error": "N8N response missing 'Course Name' field. Expected structure: {\"Course Name\": \"...\", \"Course Code\": \"...\", \"Class Times\": [], \"Lab Due Dates\": [], \"Midterm Date\": \"\"}"
                }
            
            # Step 4: Add metadata to N8N response for storage
            # N8N returns: Course Name, Course Code, Class Times, Lab Due Dates, Midterm Date
            # We need to add: user_id, file_name
            n8n_data["user_id"] = user_id
            n8n_data["file_name"] = filename
            
            # If user provided course_name/course_code but N8N didn't return them, use user's input
            if course_name and not n8n_data.get("Course Name"):
                n8n_data["Course Name"] = course_name
            if course_code and not n8n_data.get("Course Code"):
                n8n_data["Course Code"] = course_code
            
            # Step 4: Store in database via Flask backend
            store_result = store_syllabus_from_n8n(n8n_data)
            
            if store_result.get("success"):
                return {
                    "success": True,
                    "data": store_result.get("data", {}),
                    "n8n_response": n8n_data  # Include original N8N response
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to store syllabus in database: {store_result.get('error')}",
                    "n8n_response": n8n_data  # Still return N8N response for debugging
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


def upload_syllabus(
    file_path: str,
    user_id: str = "default_user",
    course_name: Optional[str] = None,
    course_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a syllabus PDF to the backend (legacy function, kept for backward compatibility).
    
    NOTE: This function now redirects to N8N upload. Use upload_syllabus_to_n8n() directly.
    
    Args:
        file_path: Path to the PDF file
        user_id: User identifier
        course_name: Optional course name
        course_code: Optional course code
        
    Returns:
        Dictionary with success status and response data
    """
    # Redirect to N8N upload
    return upload_syllabus_to_n8n(file_path, user_id, course_name, course_code)


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

