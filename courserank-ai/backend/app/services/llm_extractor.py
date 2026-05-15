"""
Claude-powered grading extractor.

Takes syllabus text and uses Claude (haiku) to extract grading components
as structured JSON. Handles messy/inconsistent formatting that the regex
extractor cannot, and is explicitly instructed to ignore pass/fail
requirement clauses.

Falls back to None on any error so the caller can use the regex extractor.
"""
import json
import os
import re
from typing import Optional

from app.services.grading_extractor import (
    ExtractionResult,
    GradingComponentRaw,
    _normalize_and_merge,
    _calculate_confidence,
)

try:
    from anthropic import Anthropic
    _client: Optional[Anthropic] = None
except ImportError:
    Anthropic = None
    _client = None


MODEL = "claude-haiku-4-5-20251001"
MAX_TEXT_CHARS = 25_000  # ~6k tokens — plenty for any syllabus

SYSTEM_PROMPT = """You extract course grading breakdowns from university syllabus text.

Return a JSON object with one key "components", whose value is an array of objects:
  {"name": "<component name>", "weight": <percentage as number>}

Rules:
- Only include actual graded deliverables that contribute a percentage to the final grade
  (e.g. "Midterm 30%", "Final Exam 40%", "Assignments 30%", "Labs 10%", "Participation 5%").
- IGNORE pass/fail requirements like "you must score 50% on the final to pass the course",
  "minimum 60% required on the final exam", "students must achieve at least X%".
  These are eligibility thresholds, not grading components.
- IGNORE late penalty clauses (e.g. "10% per day late"), bonus marks, and total/sum rows.
- IGNORE date-only rows or schedule entries.
- Component names should be short (1-4 words), e.g. "Midterm", "Final Exam", "Assignments",
  "Quizzes", "Labs", "Project", "Participation".
- If multiple instances of the same component exist (e.g. "Assignment 1: 10%, Assignment 2: 10%"),
  combine them: {"name": "Assignments", "weight": 20}.
- In a grading table row, the LAST percentage number is ALWAYS the component's total weight.
  Ignore any intermediate percentages (like "5% each") that appear mid-row.
  Example row: "Assignments (12 assignments, 5% each) 55%" → {"name": "Assignments", "weight": 55}
  (use 55, the last number — not 5 the per-item weight, not 60 the computed product)
- If a component lists a per-item weight with a count and NO explicit total (e.g. "12 assignments worth 5% each",
  "10 quizzes, each 2%", "5 labs × 4%"), then compute total = count × per-item weight.
  Example: "11 assignments count toward grade, each worth 5%" → {"name": "Assignments", "weight": 55}
- Weights should be numbers (no % sign), e.g. 30 or 27.5.
- If you cannot find a clear grading breakdown, return {"components": []}.
- Return ONLY the JSON object. No prose, no markdown fences."""


def _get_client() -> Optional[Anthropic]:
    global _client
    if _client is not None:
        return _client
    if Anthropic is None:
        return None
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    _client = Anthropic(api_key=api_key)
    return _client


def extract_grading_llm(text: str) -> Optional[ExtractionResult]:
    """Extract grading components using Claude. Returns None if API unavailable or fails."""
    client = _get_client()
    if client is None:
        return None

    snippet = text[:MAX_TEXT_CHARS]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {"role": "user", "content": f"Syllabus text:\n\n{snippet}"}
            ],
        )
    except Exception as e:
        print(f"[llm_extractor] API call failed: {e}")
        return None

    raw = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ).strip()

    parsed = _parse_json_response(raw)
    if parsed is None:
        return None

    components: list[GradingComponentRaw] = []
    for item in parsed:
        name = str(item.get("name", "")).strip()
        try:
            weight = float(item.get("weight", 0))
        except (TypeError, ValueError):
            continue
        if not name or weight <= 0 or weight > 100:
            continue
        components.append(GradingComponentRaw(name=name, weight=weight, source="llm"))

    components = _normalize_and_merge(components)
    result = ExtractionResult(components=components)
    result.notes.append("Extracted via Claude API.")
    result.confidence_score = _calculate_confidence(components, result.notes)
    return result


def _parse_json_response(raw: str) -> Optional[list]:
    """Parse the JSON object returned by Claude. Tolerant of stray markdown fences."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            obj = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    if isinstance(obj, dict):
        components = obj.get("components")
        if isinstance(components, list):
            return components
    if isinstance(obj, list):
        return obj
    return None
