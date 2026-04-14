from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ndqs:ndqs@localhost:5432/ndqs"
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_REFRESH_SECRET: str = "change-me-in-production"
    OPENROUTER_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
