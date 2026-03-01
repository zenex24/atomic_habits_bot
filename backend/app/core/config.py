from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    webapp_url: str = "http://localhost:8000"
    public_api_base: str = ""
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4o-mini"
    database_url: str = "sqlite+aiosqlite:///./atomic_habits.db"
    admin_panel_token: str = "change_me_admin_token"
    init_data_max_age_seconds: int = 86400
    daily_chat_limit: int = 40
    default_reminder_time: str = "09:00"
    allow_test_auth: bool = False
    test_user_id: int = 111111111

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
