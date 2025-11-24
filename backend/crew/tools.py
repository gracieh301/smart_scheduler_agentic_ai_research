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

from vector.rag import retrieve_relevant_chunks
from db.plan_ops import save_study_plan, get_study_plan, get_syllabus


class ReadSyllabusContentInput(BaseModel):
    """Input schema for read_syllabus_content tool."""
    query: str = Field(..., description="What to search for in the syllabus (e.g., 'assignment due dates', 'topics covered', 'exam schedule')")
    user_id: str = Field(..., description="User identifier to filter syllabus content")
    n_results: int = Field(default=5, description="Number of relevant chunks to retrieve")


class ReadSyllabusContentTool(BaseTool):
    name: str = "read_syllabus_content"
    description: str = """Read relevant content from the syllabus using semantic search.
    
    This tool retrieves the most relevant chunks from the uploaded syllabus PDF
    based on a query. Use this when you need to understand course topics, 
    assignments, due dates, or any other syllabus information."""
    args_schema: Type[BaseModel] = ReadSyllabusContentInput
    
    def _run(self, query: str, user_id: str, n_results: int = 5) -> str:
        try:
            results = retrieve_relevant_chunks(
                query=query,
                user_id=user_id,
                n_results=n_results
            )
            
            if not results:
                return f"No relevant content found for query: {query}"
            
            # Format results
            formatted_content = []
            for i, result in enumerate(results, 1):
                text = result.get("text", "")
                metadata = result.get("metadata", {})
                course_name = metadata.get("course_name", "Unknown Course")
                
                formatted_content.append(
                    f"[Chunk {i} from {course_name}]\n{text}\n"
                )
            
            return "\n".join(formatted_content)
            
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

