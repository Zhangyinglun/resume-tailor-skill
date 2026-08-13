#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared utilities for resume scripts: validation, JSON I/O, parsing helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REQUIRED_KEYS = ("name", "contact", "summary", "skills", "experience", "education")

_QUANTIFIED_RESULT_PATTERNS = (
    re.compile(r"(?:\d+(?:\.\d+)?\s*(?:%|x\b|×))", re.IGNORECASE),
    re.compile(
        r"(?:[$€£¥]\s*\d|\d+(?:\.\d+)?\s*(?:ms|milliseconds?|seconds?|minutes?|hours?|days?|weeks?|months?|years?))",
        re.IGNORECASE,
    ),
    re.compile(
        r"\d+(?:\.\d+)?\s*(?:users?|customers?|requests?|transactions?|records?|events?|services?|engineers?|people|deployments?)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:from\s+\d+(?:\.\d+)?\s+to\s+\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:uptime|latency|revenue|cost))", re.IGNORECASE),
)

_ACTION_VERB_RE = re.compile(
    r"^(?:achieved|automated|built|created|delivered|designed|developed|drove|enabled|engineered|established|executed|expanded|generated|grew|implemented|improved|increased|integrated|launched|led|managed|migrated|modernized|optimized|orchestrated|reduced|refactored|resolved|scaled|secured|simplified|standardized|streamlined|transformed|upgraded)\b",
    re.IGNORECASE,
)
_METHOD_MARKER_RE = re.compile(
    r"\b(?:by|through|using|via|with|leveraging|on|across)\b", re.IGNORECASE
)

_SKILL_REQUIRED = ("category", "items")
_EXPERIENCE_REQUIRED = ("company", "title", "dates", "bullets")
_EDUCATION_REQUIRED = ("school", "degree", "dates")


def validate_resume_content(
    payload: dict[str, Any], *, require_non_empty: bool = False
) -> None:
    """Validate resume JSON has required keys and correct types.

    When *require_non_empty* is True the list fields must also be non-empty
    (used by the PDF generator).  Otherwise only type checks are performed
    (used by the cache manager and template renderer).
    """
    missing = [key for key in REQUIRED_KEYS if key not in payload]
    if missing:
        raise ValueError(f"Input content missing required fields: {', '.join(missing)}")

    for key in ("name", "contact", "summary"):
        value = payload[key]
        if not isinstance(value, str):
            raise ValueError(f"`{key}` must be a string.")
        if require_non_empty and not value.strip():
            raise ValueError(f"`{key}` must be non-empty.")

    for key in ("skills", "experience", "education"):
        value = payload[key]
        if not isinstance(value, list):
            raise ValueError(f"`{key}` must be an array.")
        if require_non_empty and not value:
            raise ValueError(f"`{key}` must be a non-empty array.")

    # -- Nested field validation for skills --
    for i, entry in enumerate(payload["skills"]):
        if not isinstance(entry, dict):
            raise ValueError(f"skills[{i}] must be an object")
        for field in _SKILL_REQUIRED:
            if field not in entry:
                raise ValueError(f"skills[{i}] missing required field: {field}")
        if not isinstance(entry["category"], str):
            raise ValueError(f"skills[{i}].category must be a str")
        if not isinstance(entry["items"], str):
            raise ValueError(f"skills[{i}].items must be a str")

    # -- Nested field validation for experience --
    for i, entry in enumerate(payload["experience"]):
        if not isinstance(entry, dict):
            raise ValueError(f"experience[{i}] must be an object")
        for field in _EXPERIENCE_REQUIRED:
            if field not in entry:
                raise ValueError(f"experience[{i}] missing required field: {field}")
        for field in ("company", "title", "dates"):
            if not isinstance(entry[field], str):
                raise ValueError(f"experience[{i}].{field} must be a str")
        if "location" in entry and not isinstance(entry["location"], str):
            raise ValueError(f"experience[{i}].location must be a str")
        if not isinstance(entry["bullets"], list):
            raise ValueError(f"experience[{i}].bullets must be a list")
        for j, bullet in enumerate(entry["bullets"]):
            if not isinstance(bullet, str):
                raise ValueError(f"experience[{i}].bullets[{j}] must be a str")

    # -- Nested field validation for education --
    for i, entry in enumerate(payload["education"]):
        if not isinstance(entry, dict):
            raise ValueError(f"education[{i}] must be an object")
        for field in _EDUCATION_REQUIRED:
            if field not in entry:
                raise ValueError(f"education[{i}] missing required field: {field}")
        if not isinstance(entry["school"], str):
            raise ValueError(f"education[{i}].school must be a str")
        if not isinstance(entry["degree"], str):
            raise ValueError(f"education[{i}].degree must be a str")
        if not isinstance(entry["dates"], str):
            raise ValueError(f"education[{i}].dates must be a str")
        if "location" in entry and not isinstance(entry["location"], str):
            raise ValueError(f"education[{i}].location must be a str")

    optional_specs: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        "projects": (("name", "bullets"), ("name", "tech", "dates")),
        "certifications": (("name",), ("name", "issuer", "dates")),
        "awards": (("name",), ("name", "organization", "dates")),
    }
    for key, (required_fields, string_fields) in optional_specs.items():
        entries = payload.get(key, [])
        if not isinstance(entries, list):
            raise ValueError(f"`{key}` must be an array when provided.")
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"{key}[{i}] must be an object")
            for field in required_fields:
                if field not in entry:
                    raise ValueError(f"{key}[{i}] missing required field: {field}")
            for field in string_fields:
                if field in entry and not isinstance(entry[field], str):
                    raise ValueError(f"{key}[{i}].{field} must be a str")
            if "bullets" in entry:
                if not isinstance(entry["bullets"], list):
                    raise ValueError(f"{key}[{i}].bullets must be a list")
                for j, bullet in enumerate(entry["bullets"]):
                    if not isinstance(bullet, str):
                        raise ValueError(f"{key}[{i}].bullets[{j}] must be a str")


def load_json_file(path: Path) -> dict[str, Any]:
    """Read a JSON file and return the top-level dict."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"File does not exist: {path}") from None
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return payload


def write_json_file(path: Path, payload: dict[str, Any]) -> Path:
    """Atomically write *payload* as pretty-printed UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return path


def collect_bullets(
    resume: dict[str, Any], *, include_projects: bool = True
) -> list[str]:
    """Collect bullet strings from experience (and optionally projects)."""
    bullets: list[str] = []
    for exp in resume.get("experience", []):
        bullets.extend(exp.get("bullets", []))
    if include_projects:
        for proj in resume.get("projects", []):
            bullets.extend(proj.get("bullets", []))
    return bullets


def _extract_terms(keyword_list: list[Any]) -> list[str]:
    """Extract term strings from keyword list (supports both str and dict format)."""
    terms: list[str] = []
    for item in keyword_list:
        if isinstance(item, str):
            terms.append(item.lower())
        elif isinstance(item, dict) and "term" in item:
            terms.append(str(item["term"]).lower())
    return list(dict.fromkeys(term for term in terms if term.strip()))


extract_terms = _extract_terms


def term_matches(text: str, term: str) -> bool:
    """Return whether *term* occurs as a boundary-aware phrase in *text*.

    Alphanumeric edges require word boundaries while technical punctuation in
    terms such as ``C++``, ``C#``, and ``.NET`` remains matchable.
    """
    normalized_term = " ".join(term.casefold().split())
    if not normalized_term:
        return False
    normalized_text = " ".join(text.casefold().split())
    left = r"(?<!\w)" if normalized_term[0].isalnum() else ""
    right = r"(?!\w)" if normalized_term[-1].isalnum() else ""
    return bool(re.search(f"{left}{re.escape(normalized_term)}{right}", normalized_text))


def has_quantified_result(text: str) -> bool:
    """Detect result-oriented quantities without counting bare version numbers."""
    return any(pattern.search(text) for pattern in _QUANTIFIED_RESULT_PATTERNS)


def score_bullet(
    bullet: str,
    p1_terms: list[str],
    p2_terms: list[str],
    p3_terms: list[str],
) -> dict[str, Any]:
    """Score a single bullet against JD keyword tiers.

    Scoring rules:
    - P1 keyword hit: +3 per unique keyword
    - P2 keyword hit: +2 per unique keyword
    - P3 keyword hit: +1 per unique keyword
    - Contains quantification (number): +1
    - Four-element completeness (action + keyword + method + result pattern): +1

    Returns dict with score breakdown.
    """
    p1_hits = [term for term in p1_terms if term_matches(bullet, term)]
    p2_hits = [term for term in p2_terms if term_matches(bullet, term)]
    p3_hits = [term for term in p3_terms if term_matches(bullet, term)]

    has_number = has_quantified_result(bullet)
    has_action = bool(_ACTION_VERB_RE.search(bullet.strip()))
    has_method = bool(_METHOD_MARKER_RE.search(bullet))
    has_four_elements = (
        has_number
        and has_action
        and has_method
        and (p1_hits or p2_hits or p3_hits)
        and len(bullet.split()) >= 8
    )

    score = (
        len(p1_hits) * 3
        + len(p2_hits) * 2
        + len(p3_hits) * 1
        + (1 if has_number else 0)
        + (1 if has_four_elements else 0)
    )

    return {
        "score": score,
        "p1_hits": p1_hits,
        "p2_hits": p2_hits,
        "p3_hits": p3_hits,
        "has_quantification": has_number,
        "has_action": has_action,
        "has_method": has_method,
        "has_four_elements": has_four_elements,
    }


def score_all_bullets(
    resume: dict[str, Any], jd_analysis: dict[str, Any]
) -> list[dict[str, Any]]:
    """Score all experience bullets against JD keywords.

    Returns list of scored entries with path, text, and score breakdown.
    """
    keywords = jd_analysis.get("keywords", {})
    p1_terms = _extract_terms(keywords.get("P1", []))
    p2_terms = _extract_terms(keywords.get("P2", []))
    p3_terms = _extract_terms(keywords.get("P3", []))

    scored: list[dict[str, Any]] = []
    for section in ("experience", "projects"):
        for i, item in enumerate(resume.get(section, [])):
            for j, bullet in enumerate(item.get("bullets", [])):
                result = score_bullet(str(bullet), p1_terms, p2_terms, p3_terms)
                scored.append(
                    {
                        "path": f"{section}[{i}].bullets[{j}]",
                        "text": str(bullet),
                        **result,
                    }
                )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def parse_pipe_delimited_items(
    lines: list[str],
    field_names: tuple[str, str, str],
    default_name: str,
) -> list[dict[str, str]]:
    """Parse lines of ``name | field2 | field3`` into dicts.

    *field_names* maps positional parts to dict keys (e.g.
    ``("name", "issuer", "dates")``).  *default_name* is used as the
    placeholder when the first part is empty (e.g. ``"[Certification]"``).
    """
    items: list[dict[str, str]] = []
    for line in lines:
        cleaned = line.lstrip("-\u2022 ").strip()
        if not cleaned:
            continue
        parts = [item.strip() for item in cleaned.split("|")]
        items.append(
            {
                field_names[0]: parts[0] if parts else default_name,
                field_names[1]: parts[1] if len(parts) > 1 else "",
                field_names[2]: parts[2] if len(parts) > 2 else "",
            }
        )
    return items
