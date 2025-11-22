"""Crew definition for Smart Scheduler"""
from crewai import Crew, Agent, Task
from crewai.agent import LLM
import yaml
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load agent and task configurations
config_dir = Path(__file__).parent / "config"

def load_yaml_config(filename: str) -> dict:
    """Load YAML configuration file"""
    with open(config_dir / filename, 'r') as f:
        return yaml.safe_load(f)

def create_agent(agent_config: dict) -> Agent:
    """Create an agent from configuration"""
    return Agent(
        role=agent_config['role'],
        goal=agent_config['goal'],
        backstory=agent_config.get('backstory', ''),
        verbose=agent_config.get('verbose', True),
        allow_delegation=agent_config.get('allow_delegation', False)
    )

def create_task(task_config: dict, agent: Agent) -> Task:
    """Create a task from configuration"""
    return Task(
        description=task_config['description'],
        agent=agent,
        expected_output=task_config.get('expected_output', '')
    )

def create_crew() -> Crew:
    """Create and configure the Smart Scheduler crew"""
    # Load configurations
    agents_config = load_yaml_config('agents.yaml')
    tasks_config = load_yaml_config('tasks.yaml')
    
    # Create agents
    agents = {}
    for agent_name, agent_config in agents_config.items():
        agents[agent_name] = create_agent(agent_config)
    
    # Create tasks
    tasks = []
    for task_name, task_config in tasks_config.items():
        agent_name = task_config['agent']
        if agent_name in agents:
            task = create_task(task_config, agents[agent_name])
            tasks.append(task)
    
    # Create crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=True
    )
    
    return crew

