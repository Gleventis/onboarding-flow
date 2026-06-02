"""
Application configuration via environment variables
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings class with config loaded from env
    """
    logging_level: str = "DEBUG"
    app_name: str = "Onboarding Flow"
    database_url: str = "postgresql://onboarding:onboarding@localhost:5432/onboarding"
    token_expiry_seconds: int = 3600


settings = Settings()
