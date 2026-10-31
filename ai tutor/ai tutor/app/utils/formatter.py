"""
Utility functions for formatting and parsing responses.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any


def parse_quiz_json(raw_text: str) -> list[dict]:
    """
    Parse LLM output into a list of quiz question dicts.
    Handles common LLM quirks like markdown code blocks.
    """
    # Strip markdown code blocks if present
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        questions = json.loads(text)
        if isinstance(questions, list):
            validated = []
            for q in questions:
                validated.append({
                    "question": str(q.get("question", "")),
                    "options": list(q.get("options", [])),
                    "answer": str(q.get("answer", "")),
                    "explanation": str(q.get("explanation", "")),
                })
            return validated
    except json.JSONDecodeError:
        pass

    # Fallback: try to find JSON array in the text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            questions = json.loads(match.group())
            if isinstance(questions, list):
                return [
                    {
                        "question": str(q.get("question", "")),
                        "options": list(q.get("options", [])),
                        "answer": str(q.get("answer", "")),
                        "explanation": str(q.get("explanation", "")),
                    }
                    for q in questions
                ]
        except json.JSONDecodeError:
            pass

    return []


def format_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime to a human-readable string."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def clean_text(text: str) -> str:
    """Clean extracted text by normalizing whitespace."""
    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)
    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_response(
    success: bool = True,
    data: Any = None,
    message: str = "",
    error: str = "",
) -> dict:
    """Build a standardized API response dict."""
    response = {"success": success}
    if message:
        response["message"] = message
    if error:
        response["error"] = error
    if data is not None:
        response["data"] = data
    return response
