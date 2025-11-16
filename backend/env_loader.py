"""
Centralized environment variable loader for AURA Backend
Searches multiple locations for .env files and loads them
"""
import os
from pathlib import Path

def load_environment():
    """
    Load environment variables from multiple possible locations.
    Priority order:
    1. Environment variables (set by Render/hosting platform)
    2. backend/.env
    3. config/.env
    4. Root .env
    """
    
    # Try importing dotenv, but don't fail if it's not available
    try:
        from dotenv import load_dotenv
        dotenv_available = True
    except ImportError:
        print("⚠️ python-dotenv not installed. Using system environment variables only.")
        dotenv_available = False
    
    # Get the current file's directory
    current_dir = Path(__file__).parent.resolve()
    
    # Possible .env file locations (in order of priority)
    env_locations = [
        current_dir / '.env',                    # backend/.env
        current_dir.parent / 'config' / '.env',  # config/.env
        current_dir.parent / '.env',             # root .env
    ]
    
    # Try loading from each location
    env_loaded = False
    if dotenv_available:
        for env_path in env_locations:
            if env_path.exists():
                print(f"✅ Loading environment from: {env_path}")
                load_dotenv(env_path)
                env_loaded = True
                break
    
    if not env_loaded and not os.getenv('OPENROUTER_API_KEY'):
        print("⚠️ No .env file found. Using environment variables from hosting platform.")
    
    # Verify critical environment variables
    required_vars = ['OPENROUTER_API_KEY']
    optional_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'GITHUB_TOKEN']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        print(f"❌ ERROR: Missing required environment variables: {', '.join(missing_required)}")
        print("   Add these in your Render dashboard → Environment")
    
    if missing_optional:
        print(f"⚠️ Optional environment variables not set: {', '.join(missing_optional)}")
        print("   Some features may be limited.")
    
    if not missing_required:
        print("✅ All required environment variables loaded")
    
    return env_loaded

# Auto-load when this module is imported
load_environment()