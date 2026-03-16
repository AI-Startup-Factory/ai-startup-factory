import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from core.models import MODEL_LIST

class Settings(BaseSettings):
    # Database
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    
    # AI Keys
    OPENROUTER_API_KEY: str
    
    # Shared Lists
    MODELS: list[str] = MODEL_LIST
    
    # App Settings
    PYTHONPATH: str = os.getcwd()
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"
    )

settings = Settings()
