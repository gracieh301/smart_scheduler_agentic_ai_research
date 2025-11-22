import streamlit as st
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory or project root
backend_env = Path(__file__).parent.parent / "backend" / ".env"
root_env = Path(__file__).parent.parent / ".env"
if backend_env.exists():
    load_dotenv(backend_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()  # Fallback to current directory

st.set_page_config(
    page_title="Smart Scheduler",
    page_icon="📅",
    layout="centered"
)

st.title("📅 Smart Scheduler")
st.markdown("Upload your course syllabi (PDF format)")

# Configuration: Choose between Flask backend or direct n8n webhook
use_flask_backend = st.sidebar.checkbox("Use Flask Backend", value=True)

if use_flask_backend:
    backend_url = st.sidebar.text_input(
        "Backend URL",
        value="http://localhost:5000/upload",
        help="URL of the Flask backend endpoint"
    )
else:
    n8n_webhook_url = st.sidebar.text_input(
        "N8N Webhook URL",
        value=os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/upload"),
        help="Direct n8n webhook URL"
    )

# File uploader
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Select a PDF file containing course syllabi"
)

if uploaded_file is not None:
    st.success(f"File selected: {uploaded_file.name}")
    
    if st.button("Upload", type="primary"):
        with st.spinner("Uploading file..."):
            try:
                if use_flask_backend:
                    # Upload to Flask backend
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(backend_url, files=files)
                else:
                    # Upload directly to n8n webhook
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(n8n_webhook_url, files=files)
                
                if response.status_code == 200:
                    st.success("✅ File uploaded successfully!")
                    if use_flask_backend:
                        try:
                            result = response.json()
                            if "n8n_response" in result:
                                st.json(result)
                        except:
                            st.text(response.text)
                else:
                    st.error(f"❌ Upload failed with status code {response.status_code}")
                    st.text(response.text)
                    
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Could not connect to the server. Please make sure the backend is running.")
            except Exception as e:
                st.error(f"⚠️ An error occurred while uploading: {str(e)}")

