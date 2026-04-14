from pydantic import model_validator
from pydantic_settings import BaseSettings

_MIN_SECRET_LENGTH = 32


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

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT != "production":
            return self
        errors = []
        for field in ("JWT_SECRET_KEY", "JWT_REFRESH_SECRET"):
            value = getattr(self, field)
            if value == "change-me-in-production":
                errors.append(f"{field} must not use the default placeholder in production")
            elif len(value) < _MIN_SECRET_LENGTH:
                errors.append(f"{field} must be at least {_MIN_SECRET_LENGTH} characters")
        if errors:
            raise ValueError("; ".join(errors))
        return self


settings = Settings()
