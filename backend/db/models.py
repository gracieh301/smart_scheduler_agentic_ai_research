"""
SQLAlchemy database models for Study Plan Generator.
Uses SQLite by default (can be upgraded to PostgreSQL).
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Syllabus(Base):
    """
    Syllabus model for storing uploaded syllabus documents.
    
    Stores the raw text extracted from PDFs and metadata about the course.
    Also stores structured data from N8N (class times, due dates, etc.).
    """
    __tablename__ = 'syllabi'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)  # External user ID
    course_name = Column(String(255), nullable=False)
    course_code = Column(String(50), nullable=True)
    raw_text = Column(Text, nullable=False)  # Extracted text from PDF (for RAG)
    file_name = Column(String(255), nullable=True)
    structured_data = Column(JSON, nullable=True)  # Structured data from N8N (Class Times, Lab Due Dates, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    study_plans = relationship("StudyPlan", back_populates="syllabus", cascade="all, delete-orphan")


class StudyPlan(Base):
    """
    Study plan model for storing generated weekly study plans.
    
    Stores the complete plan structure as JSON, including all weekly schedules
    with focused study sessions and spaced repetition reviews.
    """
    __tablename__ = 'study_plans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)  # External user ID
    syllabus_id = Column(Integer, ForeignKey('syllabi.id'), nullable=True)
    plan_data = Column(JSON, nullable=False)  # Full plan structure with weekly schedules
    version = Column(Integer, default=1)  # Track plan versions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    syllabus = relationship("Syllabus", back_populates="study_plans")
    tasks = relationship("StudyTask", back_populates="plan", cascade="all, delete-orphan")


class StudyTask(Base):
    """
    Individual study task within a plan.
    
    Represents a single study session (focused study or spaced repetition review)
    scheduled for a specific date and time.
    """
    __tablename__ = 'study_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey('study_plans.id'), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)  # 'focused' or 'review' (spaced repetition)
    week_number = Column(Integer, nullable=False)  # Which week of the plan
    scheduled_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    priority = Column(Integer, default=1)  # Higher = more important
    status = Column(String(50), default='scheduled')  # 'scheduled', 'completed', 'skipped'
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    # For spaced repetition
    repetition_level = Column(Integer, default=0)  # 0=focused, 1=1day, 2=3days, 3=1week, 4=3weeks
    parent_task_id = Column(Integer, ForeignKey('study_tasks.id'), nullable=True)  # Link review to original
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plan = relationship("StudyPlan", back_populates="tasks")
    parent_task = relationship("StudyTask", remote_side=[id])


# Database initialization
def get_database_url() -> str:
    """
    Get database URL from environment or use default SQLite.
    
    Set DATABASE_URL environment variable to use PostgreSQL or other databases.
    Example: DATABASE_URL=postgresql://user:pass@localhost/dbname
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    # Default to SQLite in backend directory
    db_path = os.path.join(os.path.dirname(__file__), "..", "study_planner.db")
    return f"sqlite:///{db_path}"


def init_db() -> None:
    """
    Initialize database and create all tables.
    
    Creates the database file and all tables if they don't exist.
    Also adds missing columns to existing tables (migration support).
    """
    engine = create_engine(get_database_url(), echo=os.getenv("DB_ECHO", "False").lower() == "true")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Add missing columns to existing tables (simple migration)
    # This handles the case where we add new columns to existing models
    if 'sqlite' in get_database_url():
        # SQLite-specific migration
        try:
            with engine.connect() as conn:
                # Check if structured_data column exists
                result = conn.execute(text("PRAGMA table_info(syllabi)"))
                columns = [row[1] for row in result]
                
                if 'structured_data' not in columns:
                    print("Adding 'structured_data' column to syllabi table...")
                    with conn.begin():
                        conn.execute(text("ALTER TABLE syllabi ADD COLUMN structured_data TEXT"))
                    print("✓ Successfully added 'structured_data' column")
        except Exception as e:
            print(f"Warning: Could not add structured_data column: {e}")
            # Table might not exist yet, which is fine - it will be created with the column
    
    return engine


def get_session() -> Session:
    """
    Get a database session.
    
    Returns:
        SQLAlchemy session object. Caller should close it with session.close()
    """
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

