"""Tests for .env.example file — ensures all required env vars are documented."""

from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

REQUIRED_VARS = [
    "DATABASE_URL",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "JWT_SECRET_KEY",
    "JWT_REFRESH_SECRET",
    "OPENROUTER_API_KEY",
    "REDIS_URL",
]


@pytest.fixture()
def env_example_path() -> Path:
    return ROOT_DIR / ".env.example"


@pytest.fixture()
def env_example_content(env_example_path: Path) -> str:
    assert env_example_path.exists(), ".env.example file must exist in project root"
    return env_example_path.read_text()


def _parse_env_vars(content: str) -> dict[str, str]:
    """Parse KEY=value pairs from .env content, skipping comments and blank lines."""
    variables: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            variables[key.strip()] = value.strip()
    return variables


class TestEnvExample:
    def test_file_exists(self, env_example_path: Path) -> None:
        assert env_example_path.exists(), ".env.example must exist in project root"

    def test_contains_all_required_vars(self, env_example_content: str) -> None:
        variables = _parse_env_vars(env_example_content)
        for var in REQUIRED_VARS:
            assert var in variables, f"Missing required env var: {var}"

    def test_no_real_secrets_in_values(self, env_example_content: str) -> None:
        """Ensure .env.example has placeholder values, not real secrets."""
        variables = _parse_env_vars(env_example_content)
        for key, value in variables.items():
            if "SECRET" in key or "API_KEY" in key or "PASSWORD" in key:
                assert value == "" or value.startswith("your-") or value.startswith("change-"), (
                    f"{key} should have a placeholder value, not a real secret: {value}"
                )

    def test_each_var_has_comment(self, env_example_content: str) -> None:
        """Each env var should have a comment (line starting with #) before it."""
        lines = env_example_content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                # Look backwards for a comment line
                found_comment = False
                for j in range(i - 1, -1, -1):
                    prev = lines[j].strip()
                    if prev.startswith("#"):
                        found_comment = True
                        break
                    if prev == "":
                        continue
                    break
                key = stripped.partition("=")[0].strip()
                assert found_comment, f"Env var {key} should have a comment above it"
