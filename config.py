"""
Configuration management for QBF Logic System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent
    JAR_PATH = PROJECT_ROOT / os.getenv('TWEETY_JAR_PATH', 'org.tweetyproject.logics.qbf-1.28-with-dependencies.jar')
    
    # API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # LLM Provider settings
    DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo')
    
    # API Endpoints
    OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
    ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
    
    # Solver settings
    SOLVER_TIMEOUT = int(os.getenv('SOLVER_TIMEOUT', '30'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_api_key(cls, provider: str = None) -> str:
        """Get API key for specified provider"""
        provider = provider or cls.DEFAULT_LLM_PROVIDER
        
        if provider.lower() == 'openai':
            return cls.OPENAI_API_KEY
        elif provider.lower() == 'anthropic':
            return cls.ANTHROPIC_API_KEY
        elif provider.lower() == 'gemini':
            return cls.GEMINI_API_KEY
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check JAR file
        if not cls.JAR_PATH.exists():
            errors.append(f"TweetyProject JAR not found: {cls.JAR_PATH}")
        
        # Check API keys
        if not cls.get_api_key():
            errors.append(f"No API key found for provider: {cls.DEFAULT_LLM_PROVIDER}")
        
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True

# Validate on import
if __name__ == "__main__":
    if Config.validate_config():
        print("Configuration is valid!")
    else:
        print("Configuration has errors!")