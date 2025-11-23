"""
CrewAI crew configuration for Study Plan Generator.
Connects supervisor, agents, tasks, and tools.
"""
from crewai import Crew, Task
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

from .supervisor import create_supervisor_agent
from .agents import (
    create_study_planner_agent,
    create_tutor_agent,
    create_parsing_agent
)
from .tools import send_plan_to_n8n


def create_crew() -> Crew:
    """
    Create and configure the Study Plan Generator crew.
    
    The crew consists of:
    - Supervisor Agent: Routes requests to other agents
    - Study Planner Agent: Creates weekly study schedules
    - Tutor Agent: Answers student questions
    - Parsing Agent: Extracts syllabus information
    
    Returns:
        Configured CrewAI crew ready to process tasks
    """
    # Create all agents
    supervisor = create_supervisor_agent()
    study_planner = create_study_planner_agent()
    tutor = create_tutor_agent()
    parser = create_parsing_agent()
    
    # Create the crew
    crew = Crew(
        agents=[supervisor, study_planner, tutor, parser],
        tasks=[],  # Tasks are created dynamically based on requests
        verbose=True,
        process="sequential"  # Process tasks sequentially
    )
    
    return crew


def create_plan_generation_task(
    user_id: str,
    syllabus_id: Optional[int] = None,
    course_name: Optional[str] = None
) -> Task:
    """
    Create a task for generating a study plan.
    
    Args:
        user_id: User identifier
        syllabus_id: Optional syllabus ID to reference
        course_name: Optional course name for context
        
    Returns:
        Task configured for study plan generation
    """
    study_planner = create_study_planner_agent()
    
    description = f"""
    Generate an optimized weekly study plan for user {user_id}.
    
    Steps:
    1. Read the syllabus content using the read_syllabus_content tool to understand:
       - Course topics and their sequence
       - Assignment due dates and exam dates
       - Estimated workload per topic
    
    2. Create a structured weekly study plan with:
       - Focused study sessions for new material
       - Spaced repetition review sessions (schedule reviews at: 1 day, 3 days, 1 week, 3 weeks after initial study)
       - Proper time allocation based on topic complexity
       - Alignment with assignment and exam deadlines
    
    3. The plan should be structured as JSON with this format:
    {{
        "weeks": [
            {{
                "week_number": 1,
                "tasks": [
                    {{
                        "topic": "Introduction to Machine Learning",
                        "task_type": "focused",  // or "review"
                        "scheduled_date": "2024-01-15T10:00:00",
                        "duration_minutes": 90,
                        "priority": 2,  // 1-5, higher = more important
                        "repetition_level": 0,  // 0=focused, 1=1day, 2=3days, 3=1week, 4=3weeks
                        "notes": "Focus on supervised learning concepts"
                    }}
                ]
            }}
        ]
    }}
    
    4. Save the plan using the write_study_plan tool
    5. Optionally send the plan to n8n webhook using send_plan_to_n8n tool
    
    Course: {course_name or "Unknown"}
    Syllabus ID: {syllabus_id or "Not specified"}
    """
    
    task = Task(
        description=description,
        agent=study_planner,
        expected_output="A complete study plan saved to the database with weekly schedules including focused study and spaced repetition reviews"
    )
    
    return task


def run_plan_generation(
    user_id: str,
    syllabus_id: Optional[int] = None,
    course_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the crew to generate a study plan.
    
    Args:
        user_id: User identifier
        syllabus_id: Optional syllabus ID
        course_name: Optional course name
        
    Returns:
        Dictionary with success status and result/error message
    """
    try:
        crew = create_crew()
        task = create_plan_generation_task(
            user_id=user_id,
            syllabus_id=syllabus_id,
            course_name=course_name
        )
        
        # Add task to crew
        crew.tasks = [task]
        
        # Execute
        result = crew.kickoff()
        
        return {
            "success": True,
            "result": str(result),
            "user_id": user_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id
        }

