"""Tool for interacting with n8n webhooks"""
import requests
from typing import Optional

try:
    from crewai_tools import tool
except ImportError:
    # Fallback if crewai_tools is not available
    def tool(name):
        def decorator(func):
            func.tool_name = name
            return func
        return decorator


@tool("Send file to n8n webhook")
def send_file_to_n8n(
    webhook_url: str,
    file_path: Optional[str] = None,
    file_content: Optional[bytes] = None,
    filename: Optional[str] = None,
    mimetype: Optional[str] = None
) -> dict:
    """
    Send a file to an n8n webhook endpoint.
    
    Args:
        webhook_url: The n8n webhook URL to send the file to
        file_path: Path to the file to upload (if file is on disk)
        file_content: File content as bytes (if file is in memory)
        filename: Name of the file
        mimetype: MIME type of the file (e.g., 'application/pdf')
    
    Returns:
        dict: Response from the webhook
    """
    try:
        if file_path:
            with open(file_path, 'rb') as f:
                files = {'file': (filename or 'file', f, mimetype)}
                response = requests.post(webhook_url, files=files)
        elif file_content:
            files = {'file': (filename or 'file', file_content, mimetype)}
            response = requests.post(webhook_url, files=files)
        else:
            return {"error": "Either file_path or file_content must be provided"}
        
        if response.status_code == 200:
            try:
                return {"status": "success", "response": response.json()}
            except:
                return {"status": "success", "response": response.text}
        else:
            return {
                "status": "error",
                "status_code": response.status_code,
                "response": response.text
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

