"""
Supervisor agent for orchestrating the Study Plan Generator crew.
Routes tasks to the appropriate specialized agents.
"""
from crewai import Agent
import os
from dotenv import load_dotenv

load_dotenv()

# Import LLM configuration
from .llm_config import get_llm, print_llm_status

# Print LLM status on import
print_llm_status()

# Get LLM instance (if configured)
_llm = get_llm()


def create_supervisor_agent() -> Agent:
    """
    Create the Supervisor Agent.
    
    This agent orchestrates the specialized agents:
    - Study Planner Agent: Creates weekly study schedules
    - Parsing Agent: Extracts syllabus information
    
    The supervisor analyzes incoming requests and delegates to the appropriate agent(s).
    
    Returns:
        Configured Supervisor Agent
    """
    agent_kwargs = {
        "role": "Study Plan Supervisor",
        "goal": "Orchestrate the study plan generation process by routing tasks to specialized agents",
        "backstory": """You are an intelligent coordinator who manages a team of specialized agents
        for study plan generation. You understand when to:
        - Delegate syllabus parsing to the Parsing Agent
        - Delegate study plan creation to the Study Planner Agent
        
        You ensure that agents have the information they need and coordinate multi-step workflows
        (e.g., parse syllabus first, then generate plan).""",
        "verbose": True,
        "allow_delegation": True  # Supervisor can delegate to other agents
    }
    
    # Add LLM if configured
    if _llm is not None:
        agent_kwargs["llm"] = _llm
    
    return Agent(**agent_kwargs)



