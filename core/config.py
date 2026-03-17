# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # API Keys & URLs
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    OPENROUTER_API_KEY: str
    AI_STARTUP_TOKEN: str | None = None

    # Pipeline Limits
    MAX_SIGNALS_PER_RUN: int = 10
    MAX_IDEAS_PER_RUN: int = 10

    # Model Fallback List (Sangat Penting untuk Market Analyzer & Idea Generator)
    MODELS: List[str] = [
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen-72b-chat:free",
        "mistralai/mistral-7b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free"
    ]

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"
    )

settings = Settings()
