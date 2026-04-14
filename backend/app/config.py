from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ndqs"

    # OAuth: GitHub
    github_client_id: str = ""
    github_client_secret: str = ""

    # OAuth: Google
    google_client_id: str = ""
    google_client_secret: str = ""

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_refresh_secret: str = "change-me-refresh-in-production"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # OpenRouter
    openrouter_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # App
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
