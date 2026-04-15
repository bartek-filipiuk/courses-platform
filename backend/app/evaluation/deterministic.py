"""Deterministic evaluation — quiz, url_check, command_output."""

import re

import httpx
import structlog

logger = structlog.get_logger()


async def evaluate_deterministic(eval_type: str, payload: dict, criteria: dict) -> dict:
    """Run deterministic checks based on evaluation type."""
    if eval_type == "quiz":
        return _evaluate_quiz(payload, criteria)
    if eval_type == "url_check":
        return await _evaluate_url_check(payload, criteria)
    if eval_type == "command_output":
        return _evaluate_command_output(payload, criteria)
    return {"passed": False, "error": f"Unknown eval type: {eval_type}"}


def _evaluate_quiz(payload: dict, criteria: dict) -> dict:
    """Quiz: case-insensitive key matching."""
    selected = str(payload.get("selected_option_id", "")).strip().lower()
    correct = str(criteria.get("correct_option_id", "")).strip().lower()

    if not correct:
        return {"passed": False, "error": "No correct answer configured"}

    passed = selected == correct
    return {"passed": passed, "selected": selected, "correct": correct}


async def _evaluate_url_check(payload: dict, criteria: dict) -> dict:
    """URL check: HTTP request to student's deployed endpoint."""
    url = payload.get("url", "")
    if not url:
        return {"passed": False, "error": "No URL provided"}

    method = criteria.get("method", "GET").upper()
    expected_status = criteria.get("expected_status", 200)
    expected_body_contains = criteria.get("body_contains", None)

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.request(
                method,
                url,
                json=criteria.get("request_body"),
                headers=criteria.get("request_headers", {}),
            )

        status_ok = resp.status_code == expected_status
        body_ok = True
        if expected_body_contains:
            body_ok = expected_body_contains in resp.text

        return {
            "passed": status_ok and body_ok,
            "actual_status": resp.status_code,
            "expected_status": expected_status,
            "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
            "body_check": body_ok,
        }

    except (httpx.TimeoutException, httpx.ConnectError) as e:
        return {"passed": False, "error": f"Connection failed: {str(e)}"}


def _evaluate_command_output(payload: dict, criteria: dict) -> dict:
    """Command output: regex/pattern matching."""
    output = str(payload.get("output", ""))
    patterns = criteria.get("expected_patterns", [])

    if not patterns:
        return {"passed": True, "note": "No patterns to check"}

    results = []
    all_passed = True
    for pattern in patterns:
        match = bool(re.search(pattern, output, re.IGNORECASE | re.MULTILINE))
        results.append({"pattern": pattern, "matched": match})
        if not match:
            all_passed = False

    return {"passed": all_passed, "pattern_results": results}
