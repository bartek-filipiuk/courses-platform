"""Tests for database setup — async engine, models, Alembic config."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestDatabaseModule:
    def test_database_module_exists(self) -> None:
        from app.database import Base, async_session_factory, engine

        assert engine is not None
        assert async_session_factory is not None
        assert Base is not None

    def test_base_has_metadata(self) -> None:
        from app.database import Base

        assert Base.metadata is not None


class TestUserModel:
    def test_user_model_exists(self) -> None:
        from app.auth.models import User

        assert User is not None

    def test_user_model_has_required_columns(self) -> None:
        from app.auth.models import User

        column_names = {c.name for c in User.__table__.columns}
        required = {
            "id",
            "email",
            "display_name",
            "avatar_url",
            "provider",
            "provider_id",
            "role",
            "created_at",
            "updated_at",
        }
        assert required.issubset(column_names), f"Missing columns: {required - column_names}"

    def test_user_role_default_is_student(self) -> None:
        from app.auth.models import User

        role_col = User.__table__.c.role
        assert role_col.default is not None
        assert role_col.default.arg == "student"

    def test_user_role_enum_values(self) -> None:
        from app.auth.models import User

        role_col = User.__table__.c.role
        # Check the type has the expected enum values
        assert hasattr(role_col.type, "enums")
        assert "student" in role_col.type.enums
        assert "admin" in role_col.type.enums

    def test_user_table_name(self) -> None:
        from app.auth.models import User

        assert User.__tablename__ == "users"


class TestAlembicSetup:
    def test_alembic_ini_exists(self) -> None:
        assert (ROOT_DIR / "alembic.ini").exists()

    def test_alembic_env_exists(self) -> None:
        assert (ROOT_DIR / "alembic" / "env.py").exists()

    def test_alembic_versions_dir_exists(self) -> None:
        assert (ROOT_DIR / "alembic" / "versions").is_dir()

    def test_initial_migration_exists(self) -> None:
        versions_dir = ROOT_DIR / "alembic" / "versions"
        migrations = list(versions_dir.glob("*.py"))
        assert len(migrations) >= 1, "At least one migration file should exist"

    def test_migration_contains_users_table(self) -> None:
        versions_dir = ROOT_DIR / "alembic" / "versions"
        migrations = list(versions_dir.glob("*.py"))
        found = False
        for m in migrations:
            content = m.read_text()
            if "users" in content and "create_table" in content.lower():
                found = True
                break
        assert found, "Initial migration should create users table"
