"""
Helper functions for reading and writing study plans to the database.
Used by CrewAI tools to persist and retrieve study plans.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from .models import StudyPlan, StudyTask, Syllabus, get_session


def save_study_plan(
    user_id: str,
    plan_data: Dict[str, Any],
    syllabus_id: Optional[int] = None
) -> int:
    """
    Save a study plan to the database.
    
    Args:
        user_id: User identifier
        plan_data: Complete plan structure as JSON (should include weekly schedules)
        syllabus_id: Optional ID of the associated syllabus
        
    Returns:
        ID of the created study plan
    """
    db = get_session()
    try:
        # Deactivate any existing active plans for this user
        existing_plans = db.query(StudyPlan).filter(
            StudyPlan.user_id == user_id,
            StudyPlan.is_active == True
        ).all()
        
        for plan in existing_plans:
            plan.is_active = False
        
        # Create new plan
        new_plan = StudyPlan(
            user_id=user_id,
            syllabus_id=syllabus_id,
            plan_data=plan_data,
            is_active=True,
            version=1
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        plan_id = new_plan.id
        
        # Extract tasks from plan_data and save them
        # Expected structure: plan_data should have 'weeks' array with tasks
        if 'weeks' in plan_data:
            for week_data in plan_data['weeks']:
                week_number = week_data.get('week_number', 1)
                tasks = week_data.get('tasks', [])
                
                for task_data in tasks:
                    # Parse scheduled_date
                    scheduled_date_str = task_data.get('scheduled_date')
                    if scheduled_date_str:
                        if isinstance(scheduled_date_str, str):
                            scheduled_date = datetime.fromisoformat(scheduled_date_str.replace('Z', '+00:00'))
                        else:
                            scheduled_date = scheduled_date_str
                    else:
                        # Default to current time if not provided
                        scheduled_date = datetime.utcnow()
                    
                    study_task = StudyTask(
                        plan_id=plan_id,
                        topic=task_data.get('topic', 'Unknown'),
                        task_type=task_data.get('task_type', 'focused'),
                        week_number=week_number,
                        scheduled_date=scheduled_date,
                        duration_minutes=task_data.get('duration_minutes', 60),
                        priority=task_data.get('priority', 1),
                        repetition_level=task_data.get('repetition_level', 0),
                        notes=task_data.get('notes')
                    )
                    db.add(study_task)
        
        db.commit()
        return plan_id
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_study_plan(user_id: str, plan_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Get a study plan for a user.
    
    Args:
        user_id: User identifier
        plan_id: Optional specific plan ID. If None, returns the active plan.
        
    Returns:
        Dictionary with plan data and tasks, or None if not found
    """
    db = get_session()
    try:
        if plan_id:
            plan = db.query(StudyPlan).filter(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            ).first()
        else:
            # Get active plan
            plan = db.query(StudyPlan).filter(
                StudyPlan.user_id == user_id,
                StudyPlan.is_active == True
            ).first()
        
        if not plan:
            return None
        
        # Get all tasks for this plan
        tasks = db.query(StudyTask).filter(
            StudyTask.plan_id == plan.id
        ).order_by(StudyTask.scheduled_date).all()
        
        # Build response
        result = {
            'plan_id': plan.id,
            'user_id': plan.user_id,
            'syllabus_id': plan.syllabus_id,
            'plan_data': plan.plan_data,
            'version': plan.version,
            'is_active': plan.is_active,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
            'tasks': [
                {
                    'task_id': task.id,
                    'topic': task.topic,
                    'task_type': task.task_type,
                    'week_number': task.week_number,
                    'scheduled_date': task.scheduled_date.isoformat() if task.scheduled_date else None,
                    'duration_minutes': task.duration_minutes,
                    'priority': task.priority,
                    'status': task.status,
                    'repetition_level': task.repetition_level,
                    'notes': task.notes
                }
                for task in tasks
            ]
        }
        
        return result
        
    except Exception as e:
        raise e
    finally:
        db.close()


def get_syllabus(syllabus_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a syllabus by ID.
    
    Args:
        syllabus_id: Syllabus ID
        
    Returns:
        Dictionary with syllabus data, or None if not found
    """
    db = get_session()
    try:
        syllabus = db.query(Syllabus).filter(Syllabus.id == syllabus_id).first()
        
        if not syllabus:
            return None
        
        return {
            'id': syllabus.id,
            'user_id': syllabus.user_id,
            'course_name': syllabus.course_name,
            'course_code': syllabus.course_code,
            'raw_text': syllabus.raw_text,
            'file_name': syllabus.file_name,
            'structured_data': syllabus.structured_data,
            'created_at': syllabus.created_at.isoformat() if syllabus.created_at else None
        }
        
    except Exception as e:
        raise e
    finally:
        db.close()


def save_syllabus(
    user_id: str,
    course_name: str,
    raw_text: str,
    file_name: Optional[str] = None,
    course_code: Optional[str] = None,
    structured_data: Optional[Dict[str, Any]] = None
) -> int:
    """
    Save a syllabus to the database.
    
    Args:
        user_id: User identifier
        course_name: Name of the course
        raw_text: Extracted text from PDF (for RAG)
        file_name: Optional original filename
        course_code: Optional course code (e.g., "CS101")
        structured_data: Optional structured data from N8N (Class Times, Lab Due Dates, etc.)
        
    Returns:
        ID of the created syllabus
    """
    db = get_session()
    try:
        syllabus = Syllabus(
            user_id=user_id,
            course_name=course_name,
            course_code=course_code,
            raw_text=raw_text,
            file_name=file_name,
            structured_data=structured_data
        )
        db.add(syllabus)
        db.commit()
        db.refresh(syllabus)
        return syllabus.id
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

