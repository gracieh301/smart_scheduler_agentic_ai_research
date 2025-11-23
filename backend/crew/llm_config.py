"""
LLM configuration for CrewAI agents.
Supports OpenAI, Groq, and Mistral as LLM providers.
"""
import os
from dotenv import load_dotenv
from typing import Optional, Any

load_dotenv()

# UPDATE THIS: Set LLM_PROVIDER to "openai", "groq", or "mistral" (defaults to "openai")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# UPDATE THIS: Set GROQ_MODEL to use a different Groq model
# Available models (as of 2024):
# - "llama-3.1-70b-versatile" (high quality, slower)
# - "llama-3.1-8b-instant" (fast, good quality)
# - "mixtral-8x7b-32768" (high quality, large context)
# - "gemma-7b-it" (fast, efficient)
# - "llama-3.2-3b-preview" (very fast, smaller model)
# Note: Model names may change - check https://console.groq.com/docs/models for latest
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Mistral configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
# UPDATE THIS: Set MISTRAL_MODEL to use a different Mistral model
# Valid models (check https://docs.mistral.ai/capabilities/models/ for latest):
# - "mistral-large-latest" (default - best quality, latest version)
# - "mistral-medium-latest" (good balance)
# - "mistral-small-latest" (fast, efficient)
# - "pixtral-12b-2409" (multimodal, image support)
# - "open-mistral-7b" (open source, very fast)
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "open-mistral-7b")


def get_llm() -> Optional[Any]:
    """
    Get LLM instance for CrewAI agents.
    
    CrewAI can accept an LLM object directly, or use environment variables.
    This function configures the LLM based on LLM_PROVIDER setting.
    
    Returns:
        LLM instance or None (CrewAI will use environment variables)
    """
    try:
        if LLM_PROVIDER == "groq":
            if not GROQ_API_KEY:
                print("Warning: GROQ_API_KEY not set. Falling back to OpenAI or default.")
                # Try OpenAI as fallback
                if OPENAI_API_KEY:
                    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
                    return None
                return None
            
            # Import Groq LLM from LangChain
            try:
                from langchain_groq import ChatGroq
                
                # Set environment variable for CrewAI/LangChain
                os.environ["GROQ_API_KEY"] = GROQ_API_KEY
                
                # Create and return Groq LLM instance
                try:
                    llm = ChatGroq(
                        model=GROQ_MODEL,
                        temperature=0.7,
                        groq_api_key=GROQ_API_KEY
                    )
                    
                    print(f"✓ Configured Groq LLM: {GROQ_MODEL}")
                    return llm
                except Exception as e:
                    error_msg = str(e)
                    print(f"\n✗ Error creating Groq LLM with model '{GROQ_MODEL}': {error_msg}")
                    
                    # Check for common model name errors
                    if "llama-3.3" in GROQ_MODEL:
                        print(f"\n⚠️  WARNING: Model 'llama-3.3-70b-versatile' does NOT exist!")
                        print(f"   Use 'llama-3.1-70b-versatile' instead.")
                        print(f"   Update your .env file: GROQ_MODEL=llama-3.1-70b-versatile")
                    
                    print(f"\nValid Groq models:")
                    print(f"  - llama-3.1-70b-versatile (recommended)")
                    print(f"  - llama-3.1-8b-instant")
                    print(f"  - mixtral-8x7b-32768")
                    print(f"  - gemma-7b-it")
                    print(f"  - llama-3.2-3b-preview")
                    print(f"\nCheck https://console.groq.com/docs/models for latest models")
                    print("Falling back to environment variable configuration.")
                    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
                    return None
                
            except ImportError:
                print("Warning: langchain-groq not installed. Install with: pip install langchain-groq")
                print("Falling back to environment variable configuration.")
                os.environ["GROQ_API_KEY"] = GROQ_API_KEY
                return None
        
        elif LLM_PROVIDER == "mistral":
            if not MISTRAL_API_KEY:
                print("Warning: MISTRAL_API_KEY not set. Falling back to OpenAI or default.")
                # Try OpenAI as fallback
                if OPENAI_API_KEY:
                    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
                    return None
                # Try Groq as fallback
                if GROQ_API_KEY:
                    try:
                        from langchain_groq import ChatGroq
                        os.environ["GROQ_API_KEY"] = GROQ_API_KEY
                        llm = ChatGroq(
                            model=GROQ_MODEL,
                            temperature=0.7,
                            groq_api_key=GROQ_API_KEY
                        )
                        print(f"✓ Using Groq as fallback: {GROQ_MODEL}")
                        return llm
                    except ImportError:
                        pass
                return None
            
            # Import Mistral LLM from LangChain
            try:
                from langchain_mistralai import ChatMistralAI
                
                # Set environment variable for CrewAI/LangChain
                os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY
                
                # Create and return Mistral LLM instance
                try:
                    llm = ChatMistralAI(
                        model=MISTRAL_MODEL,
                        temperature=0.7,
                        mistral_api_key=MISTRAL_API_KEY
                    )
                    
                    print(f"✓ Configured Mistral LLM: {MISTRAL_MODEL}")
                    return llm
                except Exception as e:
                    error_msg = str(e)
                    print(f"\n✗ Error creating Mistral LLM with model '{MISTRAL_MODEL}': {error_msg}")
                    
                    print(f"\nValid Mistral models:")
                    print(f"  - mistral-large-latest (recommended)")
                    print(f"  - mistral-medium-latest")
                    print(f"  - mistral-small-latest")
                    print(f"  - pixtral-12b-2409")
                    print(f"  - open-mistral-7b")
                    print(f"\nCheck https://docs.mistral.ai/capabilities/models/ for latest models")
                    print("Falling back to environment variable configuration.")
                    os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY
                    return None
                
            except ImportError:
                print("Warning: langchain-mistralai not installed. Install with: pip install langchain-mistralai")
                print("Falling back to environment variable configuration.")
                os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY
                return None
        
        elif LLM_PROVIDER == "openai":
            if not OPENAI_API_KEY:
                print("Warning: OPENAI_API_KEY not set. Trying fallback providers...")
                # Try Mistral as fallback first
                if MISTRAL_API_KEY:
                    try:
                        from langchain_mistralai import ChatMistralAI
                        os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY
                        llm = ChatMistralAI(
                            model=MISTRAL_MODEL,
                            temperature=0.7,
                            mistral_api_key=MISTRAL_API_KEY
                        )
                        print(f"✓ Using Mistral as fallback: {MISTRAL_MODEL}")
                        return llm
                    except ImportError:
                        pass
                    except Exception:
                        pass
                # Try Groq as fallback
                if GROQ_API_KEY:
                    try:
                        from langchain_groq import ChatGroq
                        os.environ["GROQ_API_KEY"] = GROQ_API_KEY
                        llm = ChatGroq(
                            model=GROQ_MODEL,
                            temperature=0.7,
                            groq_api_key=GROQ_API_KEY
                        )
                        print(f"✓ Using Groq as fallback: {GROQ_MODEL}")
                        return llm
                    except ImportError:
                        print("Warning: langchain-groq not installed. Cannot use Groq fallback.")
                return None
            
            # OpenAI is the default - CrewAI will use OPENAI_API_KEY from environment
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
            return None
        
        else:
            print(f"Warning: Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Using default.")
            return None
            
    except Exception as e:
        print(f"Error configuring LLM: {e}")
        print("Falling back to environment variable configuration.")
        return None


def get_llm_model_name() -> str:
    """
    Get the model name based on the selected provider.
    
    Returns:
        Model name string
    """
    if LLM_PROVIDER == "groq":
        return GROQ_MODEL
    elif LLM_PROVIDER == "mistral":
        return MISTRAL_MODEL
    else:
        return OPENAI_MODEL


def print_llm_status():
    """Print current LLM configuration status."""
    print(f"\n{'='*50}")
    print(f"LLM Configuration")
    print(f"{'='*50}")
    print(f"Provider: {LLM_PROVIDER}")
    
    if LLM_PROVIDER == "groq":
        if GROQ_API_KEY:
            print(f"✓ Groq API key configured")
            print(f"  Model: {GROQ_MODEL}")
            
            # Warn about common model name mistakes
            if "llama-3.3" in GROQ_MODEL:
                print(f"\n⚠️  WARNING: Model '{GROQ_MODEL}' does NOT exist!")
                print(f"   Use 'llama-3.1-70b-versatile' instead.")
                print(f"   Update your .env file: GROQ_MODEL=llama-3.1-70b-versatile")
            
            print(f"  Note: Check https://console.groq.com/docs/models for available models")
        else:
            print("✗ Groq API key not set (GROQ_API_KEY)")
            print("  Set GROQ_API_KEY in .env file")
    elif LLM_PROVIDER == "mistral":
        if MISTRAL_API_KEY:
            print(f"✓ Mistral API key configured")
            print(f"  Model: {MISTRAL_MODEL}")
            print(f"  Note: Check https://docs.mistral.ai/capabilities/models/ for available models")
        else:
            print("✗ Mistral API key not set (MISTRAL_API_KEY)")
            print("  Set MISTRAL_API_KEY in .env file")
            print("  Get your API key from: https://console.mistral.ai/")
    else:
        if OPENAI_API_KEY:
            print(f"✓ OpenAI API key configured")
            print(f"  Model: {OPENAI_MODEL}")
        else:
            print("✗ OpenAI API key not set (OPENAI_API_KEY)")
            print("  Set OPENAI_API_KEY in .env file")
    
    print(f"{'='*50}\n")

