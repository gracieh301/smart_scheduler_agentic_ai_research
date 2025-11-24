"""
CrewAI agents for Study Plan Generator.
Defines three specialized agents: Study Planner, Tutor/Explanation, and Parsing.
"""
from crewai import Agent
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Import tools
from .tools import read_syllabus_content, write_study_plan, get_existing_plan
from .llm_config import get_llm, print_llm_status

# Print LLM status on import
print_llm_status()

# Get LLM instance (if configured)
_llm = get_llm()


def create_study_planner_agent() -> Agent:
    """
    Create the Study Planner Agent.
    
    This agent produces optimized weekly learning schedules with focused study
    sessions and spaced repetition reviews. It analyzes syllabus content and
    creates structured JSON plans.
    
    Returns:
        Configured Study Planner Agent
    """
    agent_kwargs = {
        "role": "Study Plan Generator",
        "goal": "Create optimized weekly study schedules with focused study sessions and spaced repetition reviews based on course syllabi",
        "backstory": """You are an expert educational planner with deep knowledge of learning science,
        spaced repetition algorithms, and cognitive load theory. You create study plans that maximize
        retention while respecting students' time constraints. You understand that effective learning
        requires both focused study sessions and strategic review sessions spaced over time.""",
        "verbose": True,
        "allow_delegation": False,
        "tools": [read_syllabus_content, write_study_plan, get_existing_plan]
    }
    
    # Add LLM if configured
    if _llm is not None:
        agent_kwargs["llm"] = _llm
    
    return Agent(**agent_kwargs)


def create_tutor_agent() -> Agent:
    """
    Create the Tutor/Explanation Agent.
    
    This agent answers conceptual student questions using RAG to retrieve
    relevant syllabus content. It provides explanations and clarifications.
    
    Returns:
        Configured Tutor Agent
    """
    agent_kwargs = {
        "role": "Educational Tutor",
        "goal": "Answer student questions about course content using syllabus information and provide clear explanations",
        "backstory": """You are a patient and knowledgeable tutor who helps students understand course
        material. You use the syllabus content to provide accurate, context-aware answers. You
        break down complex concepts into understandable parts and provide examples when helpful.""",
        "verbose": True,
        "allow_delegation": False,
        "tools": [read_syllabus_content]
    }
    
    # Add LLM if configured
    if _llm is not None:
        agent_kwargs["llm"] = _llm
    
    return Agent(**agent_kwargs)


def create_parsing_agent() -> Agent:
    """
    Create the Parsing Agent.
    
    This agent extracts key information from syllabus content: dates, assessments,
    topics, and workload estimates. It structures this information for use by
    the Study Planner Agent.
    
    Returns:
        Configured Parsing Agent
    """
    agent_kwargs = {
        "role": "Syllabus Parser",
        "goal": "Extract key dates, assessments, topics, and workload information from syllabus documents",
        "backstory": """You are a meticulous document analyst specializing in academic syllabi.
        You identify important dates (assignments, exams, project deadlines), extract course topics,
        and estimate workload. You structure this information clearly for other agents to use.""",
        "verbose": True,
        "allow_delegation": False,
        "tools": [read_syllabus_content]
    }
    
    # Add LLM if configured
    if _llm is not None:
        agent_kwargs["llm"] = _llm
    
    return Agent(**agent_kwargs)



