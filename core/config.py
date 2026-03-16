from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys & URLs
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    OPENROUTER_API_KEY: str
    AI_STARTUP_TOKEN: str | None = None

    # Pipeline Limits (Tambahkan baris ini)
    MAX_SIGNALS_PER_RUN: int = 20
    MAX_IDEAS_PER_RUN: int = 50

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"
    )

settings = Settings()
