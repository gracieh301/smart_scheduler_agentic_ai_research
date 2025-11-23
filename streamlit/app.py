"""
Streamlit UI for Study Plan Generator.
Allows students to upload syllabus PDFs and generate optimized study plans.
"""
import streamlit as st
import os
from pathlib import Path
from api_client import upload_syllabus, generate_plan, health_check
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Study Plan Generator",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"
if "syllabus_id" not in st.session_state:
    st.session_state.syllabus_id = None
if "plan_data" not in st.session_state:
    st.session_state.plan_data = None


def main():
    """Main Streamlit application."""
    st.title("📚 Study Plan Generator")
    st.markdown("Upload your course syllabus and get an optimized weekly study schedule with spaced repetition!")
    
    # Sidebar for user settings
    with st.sidebar:
        st.header("Settings")
        user_id = st.text_input(
            "User ID",
            value=st.session_state.user_id,
            help="Enter your user identifier"
        )
        st.session_state.user_id = user_id
        
        # N8N Configuration Info
        st.subheader("Configuration")
        n8n_url = os.getenv("N8N_WEBHOOK_URL", "")
        if n8n_url:
            st.success("✅ N8N webhook configured")
            st.caption(f"URL: {n8n_url[:50]}...")
        else:
            st.warning("⚠️ N8N webhook not configured")
            st.caption("Set N8N_WEBHOOK_URL in .env file")
        
        # Health check
        st.subheader("Backend Status")
        st.caption("Backend is used for plan generation (CrewAI + RAG)")
        if st.button("Check Backend"):
            result = health_check()
            if result.get("success"):
                st.success("✅ Backend is healthy")
                st.json(result.get("data", {}))
            else:
                st.error(f"❌ Backend error: {result.get('error')}")
    
    # Main content area
    tab1, tab2 = st.tabs(["Upload Syllabus", "Generate Plan"])
    
    with tab1:
        st.header("Upload Syllabus")
        st.markdown("Upload a PDF of your course syllabus. The file will be sent directly to N8N for processing.")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload your course syllabus as a PDF"
        )
        
        course_name = st.text_input(
            "Course Name (optional)",
            help="Enter the name of the course"
        )
        
        course_code = st.text_input(
            "Course Code (optional)",
            help="Enter the course code (e.g., CS101)"
        )
        
        if st.button("Upload Syllabus", type="primary"):
            if uploaded_file is None:
                st.error("Please upload a PDF file first")
            else:
                with st.spinner("Uploading syllabus to N8N... This will be processed by your N8N workflow."):
                    # Save uploaded file temporarily
                    temp_path = Path("temp_syllabus.pdf")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Upload directly to N8N webhook
                    from api_client import upload_syllabus_to_n8n
                    result = upload_syllabus_to_n8n(
                        file_path=str(temp_path),
                        user_id=st.session_state.user_id,
                        course_name=course_name or None,
                        course_code=course_code or None
                    )
                    
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
                    
                    if result.get("success"):
                        data = result.get("data", {})
                        # Get syllabus_id from the stored syllabus
                        syllabus_id = data.get("syllabus_id")
                        st.session_state.syllabus_id = syllabus_id
                        st.success(f"✅ Syllabus processed by N8N and stored successfully!")
                        st.info(f"📝 Syllabus ID: {syllabus_id} - Ready for study plan generation")
                        
                        # Show summary
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Course", data.get("course_name", "Unknown"))
                        with col2:
                            st.metric("Syllabus ID", syllabus_id)
                        
                        # Optionally show N8N response details
                        with st.expander("View N8N Response Details"):
                            st.json(result.get("n8n_response", {}))
                    else:
                        st.error(f"❌ Error: {result.get('error')}")
                        st.info("💡 Make sure:")
                        st.info("1. N8N_WEBHOOK_URL is set in your .env file")
                        st.info("2. N8N workflow returns JSON with: user_id, course_name, raw_text")
                        st.info("3. Flask backend is running for storing the syllabus")
    
    with tab2:
        st.header("Generate Study Plan")
        st.markdown("Generate an optimized weekly study plan based on your uploaded syllabus.")
        
        if st.session_state.syllabus_id:
            st.info(f"📄 Syllabus ID: {st.session_state.syllabus_id}")
        
        course_name_input = st.text_input(
            "Course Name (optional)",
            help="Enter course name if not uploaded with syllabus"
        )
        
        if st.button("Generate Study Plan", type="primary"):
            with st.spinner("Generating study plan... This may take a few minutes."):
                result = generate_plan(
                    user_id=st.session_state.user_id,
                    syllabus_id=st.session_state.syllabus_id,
                    course_name=course_name_input or None
                )
                
                if result.get("success"):
                    data = result.get("data", {})
                    st.session_state.plan_data = data.get("plan")
                    st.success("✅ Study plan generated successfully!")
                    
                    # Display plan
                    plan = data.get("plan")
                    if plan:
                        display_plan(plan)
                else:
                    st.error(f"❌ Error: {result.get('error')}")
        
        # Display existing plan if available
        if st.session_state.plan_data:
            st.subheader("Your Study Plan")
            display_plan(st.session_state.plan_data)


def display_plan(plan: dict):
    """
    Display the study plan in a readable format.
    
    Args:
        plan: Plan dictionary from the API
    """
    plan_data = plan.get("plan_data", {})
    weeks = plan_data.get("weeks", [])
    
    if not weeks:
        st.warning("No weekly schedule found in plan")
        st.json(plan)
        return
    
    # Display summary
    st.subheader("Plan Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Weeks", len(weeks))
    with col2:
        total_tasks = sum(len(week.get("tasks", [])) for week in weeks)
        st.metric("Total Tasks", total_tasks)
    with col3:
        focused_tasks = sum(
            len([t for t in week.get("tasks", []) if t.get("task_type") == "focused"])
            for week in weeks
        )
        st.metric("Focused Sessions", focused_tasks)
    
    # Display weekly schedule
    st.subheader("Weekly Schedule")
    
    for week in weeks:
        week_number = week.get("week_number", 0)
        tasks = week.get("tasks", [])
        
        with st.expander(f"Week {week_number} ({len(tasks)} tasks)"):
            if tasks:
                # Create a simple table
                import pandas as pd
                
                table_data = []
                for task in tasks:
                    table_data.append({
                        "Topic": task.get("topic", "Unknown"),
                        "Type": task.get("task_type", "focused"),
                        "Date": task.get("scheduled_date", "Not scheduled"),
                        "Duration (min)": task.get("duration_minutes", 60),
                        "Priority": task.get("priority", 1),
                        "Notes": task.get("notes", "")
                    })
                
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No tasks scheduled for this week")


if __name__ == "__main__":
    main()

