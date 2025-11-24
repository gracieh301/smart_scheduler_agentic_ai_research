"""
LLM configuration for CrewAI agents.
Supports OpenAI as the LLM provider.
"""
import os
from dotenv import load_dotenv
from typing import Optional, Any

load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_llm() -> Optional[Any]:
    """
    Get LLM instance for CrewAI agents.
    
    CrewAI uses environment variables by default for OpenAI.
    This function ensures OPENAI_API_KEY is set in the environment.
    
    Returns:
        None (CrewAI will use environment variables for OpenAI)
    """
    try:
        if not OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set. CrewAI will use environment variables if available.")
            return None
        
        # Set environment variable for CrewAI/LangChain
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        return None  # CrewAI uses env vars by default for OpenAI
            
    except Exception as e:
        print(f"Error configuring LLM: {e}")
        print("Falling back to environment variable configuration.")
        return None


def get_llm_model_name() -> str:
    """
    Get the OpenAI model name.
    
    Returns:
        Model name string
    """
    return OPENAI_MODEL


def print_llm_status():
    """Print current LLM configuration status."""
    print(f"\n{'='*50}")
    print(f"LLM Configuration")
    print(f"{'='*50}")
    print(f"Provider: OpenAI")
    
    if OPENAI_API_KEY:
        print(f"✓ OpenAI API key configured")
        print(f"  Model: {OPENAI_MODEL}")
    else:
        print("✗ OpenAI API key not set (OPENAI_API_KEY)")
        print("  Set OPENAI_API_KEY in .env file")
    
    print(f"{'='*50}\n")
