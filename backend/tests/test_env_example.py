"""Tests for .env.example file — verifies all required env vars are documented."""

from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = ROOT_DIR / ".env.example"

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
def env_content() -> str:
    assert ENV_EXAMPLE.exists(), f"{ENV_EXAMPLE} does not exist"
    return ENV_EXAMPLE.read_text()


@pytest.fixture()
def env_lines(env_content: str) -> list[str]:
    return env_content.strip().splitlines()


def test_env_example_exists() -> None:
    assert ENV_EXAMPLE.exists(), ".env.example must exist in project root"


def test_all_required_vars_present(env_content: str) -> None:
    for var in REQUIRED_VARS:
        assert f"{var}=" in env_content, f"Missing required variable: {var}"


def test_each_var_has_comment(env_lines: list[str]) -> None:
    """Each variable should be preceded by a comment line explaining it."""
    for var in REQUIRED_VARS:
        var_line_idx = None
        for idx, line in enumerate(env_lines):
            if line.startswith(f"{var}="):
                var_line_idx = idx
                break
        assert var_line_idx is not None, f"{var} not found in .env.example"
        # Look for a comment in the lines immediately before this variable
        has_comment = False
        for lookback in range(1, 4):  # check up to 3 lines above
            prev_idx = var_line_idx - lookback
            if prev_idx < 0:
                break
            prev_line = env_lines[prev_idx].strip()
            if prev_line.startswith("#"):
                has_comment = True
                break
            if prev_line == "":
                continue  # skip blank lines
            break  # non-comment, non-blank line → stop
        assert has_comment, f"Variable {var} must have a comment above it"


def test_no_real_secrets_in_example(env_content: str) -> None:
    """Ensure placeholder values, not real secrets."""
    lines = env_content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped == "":
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            # Values should be empty or clearly placeholder
            assert value == "" or value.startswith("your-") or value.startswith("change-"), (
                f"{key} has a non-placeholder value: {value}"
            )


def test_env_example_not_empty(env_content: str) -> None:
    assert len(env_content.strip()) > 0, ".env.example must not be empty"
