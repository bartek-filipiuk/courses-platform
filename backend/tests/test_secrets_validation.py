"""Tests for S2: Secrets in .env — BaseSettings validation for critical secrets."""

import pytest
from pydantic import ValidationError


class TestSecretsValidation:
    def test_jwt_secret_key_rejects_default_in_production(self) -> None:
        """In production, JWT_SECRET_KEY must not be the default placeholder."""
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY="change-me-in-production",
            )

    def test_jwt_refresh_secret_rejects_default_in_production(self) -> None:
        """In production, JWT_REFRESH_SECRET must not be the default placeholder."""
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY="a-real-secret-key-32chars-long!!",
                JWT_REFRESH_SECRET="change-me-in-production",
            )

    def test_jwt_secret_key_minimum_length(self) -> None:
        """JWT_SECRET_KEY must be at least 32 characters in production."""
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY="too-short",
            )

    def test_jwt_refresh_secret_minimum_length(self) -> None:
        """JWT_REFRESH_SECRET must be at least 32 characters in production."""
        from app.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY="a-real-secret-key-32chars-long!!",
                JWT_REFRESH_SECRET="short",
            )

    def test_development_allows_defaults(self) -> None:
        """In development, default placeholder values are allowed."""
        from app.config import Settings

        s = Settings(ENVIRONMENT="development")
        assert s.JWT_SECRET_KEY == "change-me-in-production"

    def test_production_accepts_proper_secrets(self) -> None:
        """Valid production secrets should be accepted."""
        from app.config import Settings

        s = Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a-real-secret-key-that-is-at-least-32-chars",
            JWT_REFRESH_SECRET="another-real-secret-key-at-least-32-chars",
        )
        assert s.ENVIRONMENT == "production"

    def test_database_url_loaded_from_settings(self) -> None:
        """DATABASE_URL must be present in settings."""
        from app.config import Settings

        s = Settings()
        assert s.DATABASE_URL is not None
        assert len(s.DATABASE_URL) > 0

    def test_settings_loads_from_env(self) -> None:
        """Settings should be loadable from env vars via BaseSettings."""
        from app.config import settings

        assert hasattr(settings, "DATABASE_URL")
        assert hasattr(settings, "JWT_SECRET_KEY")
        assert hasattr(settings, "GITHUB_CLIENT_SECRET")
        assert hasattr(settings, "OPENROUTER_API_KEY")
