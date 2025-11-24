"""
CrewAI tools for Study Plan Generator.
Provides tools for reading syllabus content and writing study plans.
"""
from crewai.tools import BaseTool
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

# Import our modules
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from db.plan_ops import save_study_plan, get_study_plan, get_syllabus


class ReadSyllabusContentInput(BaseModel):
    """Input schema for read_syllabus_content tool."""
    user_id: str = Field(..., description="User identifier to filter syllabus content")
    syllabus_id: Optional[int] = Field(default=None, description="Optional specific syllabus ID. If None, returns the most recent syllabus for the user.")


class ReadSyllabusContentTool(BaseTool):
    name: str = "read_syllabus_content"
    description: str = """Read syllabus content from the database.
    
    This tool retrieves the full syllabus text from the database for the specified user.
    Use this when you need to understand course topics, assignments, due dates, 
    or any other syllabus information. The tool returns the complete syllabus text
    extracted from the PDF."""
    args_schema: Type[BaseModel] = ReadSyllabusContentInput
    
    def _run(self, user_id: str, syllabus_id: Optional[int] = None) -> str:
        try:
            # Get syllabus from database
            if syllabus_id:
                syllabus = get_syllabus(syllabus_id)
                if not syllabus or syllabus.get('user_id') != user_id:
                    return f"No syllabus found with ID {syllabus_id} for user {user_id}"
            else:
                # Get the most recent syllabus for the user
                from db.models import Syllabus, get_session
                db = get_session()
                try:
                    syllabus_record = db.query(Syllabus).filter(
                        Syllabus.user_id == user_id
                    ).order_by(Syllabus.created_at.desc()).first()
                    
                    if not syllabus_record:
                        return f"No syllabus found for user {user_id}"
                    
                    syllabus = {
                        'id': syllabus_record.id,
                        'user_id': syllabus_record.user_id,
                        'course_name': syllabus_record.course_name,
                        'course_code': syllabus_record.course_code,
                        'raw_text': syllabus_record.raw_text,
                        'file_name': syllabus_record.file_name,
                        'structured_data': syllabus_record.structured_data,
                        'created_at': syllabus_record.created_at.isoformat() if syllabus_record.created_at else None
                    }
                finally:
                    db.close()
            
            if not syllabus:
                return f"No syllabus found for user {user_id}"
            
            # Format the syllabus content
            content_parts = []
            content_parts.append(f"Course: {syllabus.get('course_name', 'Unknown')}")
            if syllabus.get('course_code'):
                content_parts.append(f"Course Code: {syllabus.get('course_code')}")
            content_parts.append(f"Syllabus ID: {syllabus.get('id')}")
            content_parts.append("")
            content_parts.append("Syllabus Content:")
            content_parts.append("=" * 50)
            content_parts.append(syllabus.get('raw_text', ''))
            
            if syllabus.get('structured_data'):
                content_parts.append("")
                content_parts.append("Structured Data:")
                content_parts.append("=" * 50)
                import json
                content_parts.append(json.dumps(syllabus.get('structured_data'), indent=2))
            
            return "\n".join(content_parts)
            
        except Exception as e:
            return f"Error reading syllabus content: {str(e)}"


class WriteStudyPlanInput(BaseModel):
    """Input schema for write_study_plan tool."""
    user_id: str = Field(..., description="User identifier")
    plan_data: Dict[str, Any] = Field(..., description="Complete study plan structure as dictionary with weekly schedules")
    syllabus_id: Optional[int] = Field(default=None, description="Optional ID of the associated syllabus")


class WriteStudyPlanTool(BaseTool):
    name: str = "write_study_plan"
    description: str = """Write a study plan to the database.
    
    This tool saves the generated study plan so it can be retrieved later.
    The plan_data should be a structured JSON object with weekly schedules.
    
    Expected plan_data structure:
    {
        "weeks": [
            {
                "week_number": 1,
                "tasks": [
                    {
                        "topic": "Introduction to Machine Learning",
                        "task_type": "focused",  # or "review"
                        "scheduled_date": "2024-01-15T10:00:00",
                        "duration_minutes": 90,
                        "priority": 2,
                        "repetition_level": 0,
                        "notes": "Focus on supervised learning concepts"
                    }
                ]
            }
        ]
    }"""
    args_schema: Type[BaseModel] = WriteStudyPlanInput
    
    def _run(self, user_id: str, plan_data: Dict[str, Any], syllabus_id: Optional[int] = None) -> str:
        try:
            plan_id = save_study_plan(
                user_id=user_id,
                plan_data=plan_data,
                syllabus_id=syllabus_id
            )
            
            return f"Study plan saved successfully with ID: {plan_id}"
            
        except Exception as e:
            return f"Error saving study plan: {str(e)}"


class GetExistingPlanInput(BaseModel):
    """Input schema for get_existing_plan tool."""
    user_id: str = Field(..., description="User identifier")
    plan_id: Optional[int] = Field(default=None, description="Optional specific plan ID. If None, returns the active plan.")


class GetExistingPlanTool(BaseTool):
    name: str = "get_existing_plan"
    description: str = """Get an existing study plan from the database.
    
    Use this to check if a user already has a study plan before generating a new one,
    or to retrieve plan details."""
    args_schema: Type[BaseModel] = GetExistingPlanInput
    
    def _run(self, user_id: str, plan_id: Optional[int] = None) -> str:
        try:
            plan = get_study_plan(user_id=user_id, plan_id=plan_id)
            
            if not plan:
                return f"No study plan found for user {user_id}"
            
            import json
            return json.dumps(plan, indent=2, default=str)
            
        except Exception as e:
            return f"Error retrieving study plan: {str(e)}"


# Create tool instances for export
read_syllabus_content = ReadSyllabusContentTool()
write_study_plan = WriteStudyPlanTool()
get_existing_plan = GetExistingPlanTool()

