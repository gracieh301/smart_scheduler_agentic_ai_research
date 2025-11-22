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

# Initialize session state for storing uploaded files
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Initialize uploader key counter to force reset when "Add Another" is clicked
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# File uploader with dynamic key to allow clearing
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Select a PDF file containing course syllabi",
    key=f"file_uploader_{st.session_state.uploader_key}"
)

# Add file to list when uploaded
if uploaded_file is not None:
    # Check if file is already in the list
    file_already_added = any(f.get("name") == uploaded_file.name for f in st.session_state.uploaded_files)
    
    if not file_already_added:
        st.session_state.uploaded_files.append({
            "name": uploaded_file.name,
            "content": uploaded_file.getvalue(),
            "type": uploaded_file.type
        })
        st.success(f"✅ Added: {uploaded_file.name}")
        # Clear the file uploader by incrementing the key
        st.session_state.uploader_key += 1
        st.rerun()

# Display uploaded files
if st.session_state.uploaded_files:
    st.markdown("---")
    st.subheader("📚 Uploaded Syllabi")
    
    for idx, file_info in enumerate(st.session_state.uploaded_files):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"{idx + 1}. {file_info['name']}")
        with col2:
            if st.button("Remove", key=f"remove_{idx}"):
                st.session_state.uploaded_files.pop(idx)
                st.rerun()
    
    st.markdown("---")
    
    # Add Another button
    if st.button("➕ Add Another", type="secondary"):
        # Increment uploader key to clear the file uploader
        st.session_state.uploader_key += 1
        st.rerun()
    
    # Action buttons in columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Add dates to calendar button (previous functionality)
        if st.button("📅 Add dates to calendar", type="primary", use_container_width=True):
            if not st.session_state.uploaded_files:
                st.warning("⚠️ Please add at least one syllabus before adding dates to calendar.")
            else:
                with st.spinner(f"Uploading {len(st.session_state.uploaded_files)} file(s)..."):
                    try:
                        uploaded_count = 0
                        errors = []
                        
                        for file_info in st.session_state.uploaded_files:
                            try:
                                if use_flask_backend:
                                    # Upload to Flask backend
                                    files = {"file": (file_info["name"], file_info["content"], file_info["type"])}
                                    response = requests.post(backend_url, files=files)
                                else:
                                    # Upload directly to n8n webhook
                                    files = {"file": (file_info["name"], file_info["content"], file_info["type"])}
                                    response = requests.post(n8n_webhook_url, files=files)
                                
                                if response.status_code == 200:
                                    uploaded_count += 1
                                    if use_flask_backend:
                                        try:
                                            result = response.json()
                                            if "n8n_response" in result:
                                                st.json(result)
                                        except:
                                            st.text(response.text)
                                else:
                                    errors.append(f"{file_info['name']}: Status {response.status_code}")
                                    st.text(response.text)
                                    
                            except requests.exceptions.ConnectionError:
                                errors.append(f"{file_info['name']}: Connection error")
                                st.error("⚠️ Could not connect to the server. Please make sure the backend is running.")
                            except Exception as e:
                                errors.append(f"{file_info['name']}: {str(e)}")
                                st.error(f"⚠️ An error occurred while uploading {file_info['name']}: {str(e)}")
                        
                        # Display results
                        if uploaded_count == len(st.session_state.uploaded_files):
                            st.success(f"✅ Successfully uploaded {uploaded_count} file(s)! Dates added to calendar.")
                        else:
                            st.warning(f"⚠️ Uploaded {uploaded_count} out of {len(st.session_state.uploaded_files)} file(s).")
                            if errors:
                                for error in errors:
                                    st.error(error)
                        
                    except Exception as e:
                        st.error(f"⚠️ An error occurred: {str(e)}")
    
    with col2:
        # Generate Study Plan button
        if st.button("📝 Generate Study Plan", type="primary", use_container_width=True):
            if not st.session_state.uploaded_files:
                st.warning("⚠️ Please add at least one syllabus before generating a study plan.")
            else:
                with st.spinner(f"Uploading {len(st.session_state.uploaded_files)} file(s) and generating study plan..."):
                    try:
                        uploaded_count = 0
                        errors = []
                        
                        for file_info in st.session_state.uploaded_files:
                            try:
                                if use_flask_backend:
                                    # Upload to Flask backend
                                    files = {"file": (file_info["name"], file_info["content"], file_info["type"])}
                                    response = requests.post(backend_url, files=files)
                                else:
                                    # Upload directly to n8n webhook
                                    files = {"file": (file_info["name"], file_info["content"], file_info["type"])}
                                    response = requests.post(n8n_webhook_url, files=files)
                                
                                if response.status_code == 200:
                                    uploaded_count += 1
                                else:
                                    errors.append(f"{file_info['name']}: Status {response.status_code}")
                                    
                            except requests.exceptions.ConnectionError:
                                errors.append(f"{file_info['name']}: Connection error")
                            except Exception as e:
                                errors.append(f"{file_info['name']}: {str(e)}")
                        
                        # Display results
                        if uploaded_count == len(st.session_state.uploaded_files):
                            st.success(f"✅ Successfully uploaded {uploaded_count} file(s)! Study plan generation initiated.")
                            if use_flask_backend and uploaded_count > 0:
                                try:
                                    # Show response from last upload
                                    result = response.json()
                                    if "n8n_response" in result:
                                        st.json(result)
                                except:
                                    pass
                        else:
                            st.warning(f"⚠️ Uploaded {uploaded_count} out of {len(st.session_state.uploaded_files)} file(s).")
                            if errors:
                                for error in errors:
                                    st.error(error)
                        
                    except Exception as e:
                        st.error(f"⚠️ An error occurred: {str(e)}")

