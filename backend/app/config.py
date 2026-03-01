from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Atomic Habits API"
    environment: str = "dev"
    api_prefix: str = "/api/v1"
    jwt_secret: str = "change-me"
    jwt_exp_minutes: int = 60 * 24 * 14

    database_url: str = "sqlite+aiosqlite:///./atomic_habits.db"
    allow_local_auth: bool = True

    telegram_bot_token: str = ""
    telegram_webapp_url: str = "https://example.github.io/atomic-habits-miniapp/"
    default_timezone: str = "Europe/Moscow"

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_site_url: str = "http://localhost"
    openrouter_site_name: str = "Atomic Habits Coach"
    max_daily_tokens: int = 8000
    require_paid_access: bool = True
    dev_auto_paid: bool = True


settings = Settings()
