#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared utilities for resume scripts: validation, JSON I/O, parsing helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REQUIRED_KEYS = ("name", "contact", "summary", "skills", "experience", "education")

_DIGIT_RE = re.compile(r"\d")

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

    for key in ("skills", "experience", "education"):
        value = payload[key]
        if not isinstance(value, list):
            raise ValueError(f"`{key}` must be an array.")
        if require_non_empty and not value:
            raise ValueError(f"`{key}` must be a non-empty array.")

    # -- Nested field validation for skills --
    for i, entry in enumerate(payload["skills"]):
        for field in _SKILL_REQUIRED:
            if field not in entry:
                raise ValueError(f"skills[{i}] missing required field: {field}")
        if not isinstance(entry["category"], str):
            raise ValueError(f"skills[{i}].category must be a str")
        if not isinstance(entry["items"], str):
            raise ValueError(f"skills[{i}].items must be a str")

    # -- Nested field validation for experience --
    for i, entry in enumerate(payload["experience"]):
        for field in _EXPERIENCE_REQUIRED:
            if field not in entry:
                raise ValueError(f"experience[{i}] missing required field: {field}")
        if not isinstance(entry["bullets"], list):
            raise ValueError(f"experience[{i}].bullets must be a list")
        for j, bullet in enumerate(entry["bullets"]):
            if not isinstance(bullet, str):
                raise ValueError(f"experience[{i}].bullets[{j}] must be a str")

    # -- Nested field validation for education --
    for i, entry in enumerate(payload["education"]):
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
    """Write *payload* as pretty-printed JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
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
    return terms


def score_bullet(bullet: str, p1_terms: list[str], p2_terms: list[str], p3_terms: list[str]) -> dict[str, Any]:
    """Score a single bullet against JD keyword tiers.

    Scoring rules:
    - P1 keyword hit: +3 per unique keyword
    - P2 keyword hit: +2 per unique keyword
    - P3 keyword hit: +1 per unique keyword
    - Contains quantification (number): +1
    - Four-element completeness (action + keyword + method + result pattern): +1

    Returns dict with score breakdown.
    """
    text_lower = bullet.lower()

    p1_hits = [t for t in p1_terms if t in text_lower]
    p2_hits = [t for t in p2_terms if t in text_lower]
    p3_hits = [t for t in p3_terms if t in text_lower]

    has_number = bool(_DIGIT_RE.search(bullet))
    # Four-element heuristic: has verb-like start + at least one keyword hit + number
    has_four_elements = (
        has_number
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
    for i, exp in enumerate(resume.get("experience", [])):
        for j, bullet in enumerate(exp.get("bullets", [])):
            result = score_bullet(str(bullet), p1_terms, p2_terms, p3_terms)
            scored.append({
                "path": f"experience[{i}].bullets[{j}]",
                "text": str(bullet),
                **result,
            })

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
