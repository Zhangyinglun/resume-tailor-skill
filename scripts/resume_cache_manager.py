#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manage resume cache and template files (JSON format)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from collections.abc import Callable
from typing import Any

from scripts.resume_shared import (
    load_json_file,
    parse_pipe_delimited_items,
    validate_resume_content,
    write_json_file,
)

CACHE_REL_PATH = Path("cache") / "resume-working.json"
BASE_TEMPLATE_REL_PATH = Path("cache") / "base-resume.json"
JD_ANALYSIS_REL_PATH = Path("cache") / "jd-analysis.json"
_LEGACY_PATHS = (
    Path("cache") / "resume-working.md",
    Path("cache") / "base-resume.md",
)

SECTION_ALIASES = {
    "summary": "summary",
    "professional summary": "summary",
    "skills": "skills",
    "technical skills": "skills",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "education": "education",
    "projects": "projects",
    "personal projects": "projects",
    "key projects": "projects",
    "certifications": "certifications",
    "certificates": "certifications",
    "awards": "awards",
    "honors": "awards",
    "honors and awards": "awards",
}


def get_cache_path(workspace: Path) -> Path:
    return workspace / CACHE_REL_PATH


def get_base_template_path(workspace: Path) -> Path:
    return workspace / BASE_TEMPLATE_REL_PATH


def get_jd_analysis_path(workspace: Path) -> Path:
    return workspace / JD_ANALYSIS_REL_PATH


_JD_REQUIRED_KEYS = ("position", "keywords", "alignment")

_JD_KEYWORDS_REQUIRED = ("P1", "P2", "P3")


def validate_jd_analysis(payload: dict[str, Any]) -> None:
    """Validate jd-analysis.json has required structure."""
    missing = [k for k in _JD_REQUIRED_KEYS if k not in payload]
    if missing:
        raise ValueError(f"JD analysis missing required fields: {', '.join(missing)}")

    kw = payload["keywords"]
    if not isinstance(kw, dict):
        raise ValueError("`keywords` must be an object.")
    missing_tiers = [t for t in _JD_KEYWORDS_REQUIRED if t not in kw]
    if missing_tiers:
        raise ValueError(f"keywords missing required tiers: {', '.join(missing_tiers)}")
    for tier in _JD_KEYWORDS_REQUIRED:
        if not isinstance(kw[tier], list):
            raise ValueError(f"keywords.{tier} must be an array.")

    align = payload["alignment"]
    if not isinstance(align, dict):
        raise ValueError("`alignment` must be an object.")
    for field in ("matched", "gaps"):
        if field not in align:
            raise ValueError(f"alignment missing required field: {field}")
        if not isinstance(align[field], list):
            raise ValueError(f"alignment.{field} must be an array.")


def save_jd_analysis(workspace: Path, payload: dict[str, Any]) -> Path:
    """Validate and write JD analysis JSON."""
    validate_jd_analysis(payload)
    return write_json_file(get_jd_analysis_path(workspace), payload)


def read_jd_analysis(workspace: Path) -> dict[str, Any]:
    """Read JD analysis JSON."""
    return load_json_file(get_jd_analysis_path(workspace))


def reset_cache_on_start(workspace: Path) -> bool:
    removed = False
    paths = [workspace / CACHE_REL_PATH, workspace / JD_ANALYSIS_REL_PATH] + [workspace / p for p in _LEGACY_PATHS]
    for path in paths:
        if path.exists():
            path.unlink()
            removed = True
    return removed


def _normalize_heading(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z\s]", "", text).strip().lower()
    return SECTION_ALIASES.get(normalized, "")


def _extract_sections(raw_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        key: [] for key in ("summary", "skills", "experience", "education",
                            "projects", "certifications", "awards")
    }

    current_section = ""
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        maybe_section = _normalize_heading(stripped)
        if maybe_section:
            current_section = maybe_section
        elif current_section:
            sections[current_section].append(stripped)

    return sections


def _extract_header(raw_text: str) -> tuple[str, str]:
    non_empty = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not non_empty:
        return "FULL NAME", "City, State | Phone | Email | LinkedIn"

    name = non_empty[0]
    contact = ""
    for line in non_empty[1:4]:
        if "@" in line or "|" in line or "linkedin" in line.lower():
            contact = line
            break

    if not contact and len(non_empty) > 1:
        contact = non_empty[1]

    return name, contact or "City, State | Phone | Email | LinkedIn"


def _parse_skills(section_lines: list[str]) -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    for line in section_lines:
        cleaned = line.lstrip("-• ").strip()
        if not cleaned:
            continue
        if ":" in cleaned:
            category, items = cleaned.split(":", 1)
            skills.append({"category": category.strip(), "items": items.strip()})
        else:
            skills.append({"category": "Core", "items": cleaned})

    return skills or [{"category": "Core", "items": "[To be filled: Skills]"}]


def _split_tab_or_multi_space(value: str) -> list[str]:
    cleaned = value.strip()
    if not cleaned:
        return []
    if "\t" in cleaned:
        return [part.strip() for part in cleaned.split("\t") if part.strip()]
    if re.search(r"\s{2,}", cleaned):
        return [part.strip() for part in re.split(r"\s{2,}", cleaned) if part.strip()]
    return [cleaned]


def _split_two_fields(value: str, defaults: tuple[str, str]) -> tuple[str, str]:
    parts = _split_tab_or_multi_space(value)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return value.strip() or defaults[0], defaults[1]


def _make_entry(**fields: str) -> dict[str, Any]:
    """Create a placeholder entry dict with given field names and values."""
    return dict(fields)


_EXP_DEFAULTS = {"company": "[Company]", "title": "[Title]", "location": "[Location]", "dates": "[Dates]"}
_EXP_PLACEHOLDER_BULLET = "[To be filled: Experience details]"


def _parse_experience(section_lines: list[str]) -> list[dict[str, Any]]:
    experience: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in section_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        is_bullet = stripped[0] in "-•"
        cleaned = stripped.lstrip("-• ").strip()
        if not cleaned:
            continue

        if not is_bullet and "|" in cleaned:
            if current:
                if not current["bullets"]:
                    current["bullets"].append(_EXP_PLACEHOLDER_BULLET)
                experience.append(current)

            parts = [item.strip() for item in cleaned.split("|")]
            title, location, dates = "[Title]", "[Location]", "[Dates]"

            if len(parts) > 3:
                title, location, dates = parts[1], parts[2], parts[3]
            elif len(parts) == 3:
                title, location = _split_two_fields(parts[1], ("[Title]", "[Location]"))
                dates = parts[2]
            elif len(parts) == 2:
                title = parts[1]

            current = {
                "company": parts[0] if parts else "[Company]",
                "title": title, "location": location, "dates": dates,
                "bullets": [],
            }
            continue

        if current is None:
            current = {**_EXP_DEFAULTS, "bullets": []}

        current["bullets"].append(cleaned)

    if current:
        if not current["bullets"]:
            current["bullets"].append(_EXP_PLACEHOLDER_BULLET)
        experience.append(current)

    return experience or [{**_EXP_DEFAULTS, "bullets": [_EXP_PLACEHOLDER_BULLET]}]


def _parse_education(section_lines: list[str]) -> list[dict[str, str]]:
    education: list[dict[str, str]] = []
    for line in section_lines:
        cleaned = line.lstrip("-• ").strip()
        if not cleaned or "|" not in cleaned:
            continue
        parts = [item.strip() for item in cleaned.split("|")]

        if len(parts) > 3:
            degree, dates, location = parts[1], parts[2], parts[3]
        elif len(parts) > 2:
            degree, dates = parts[1], parts[2]
            location = ""
        elif len(parts) == 2:
            degree, dates = _split_two_fields(parts[1], ("[Degree]", "[Dates]"))
            location = ""
        else:
            degree, dates, location = "[Degree]", "[Dates]", ""

        entry: dict[str, str] = {
            "school": parts[0] if parts else "[School]",
            "degree": degree, "dates": dates,
        }
        if location:
            entry["location"] = location
        education.append(entry)

    return education or [{"school": "[School]", "degree": "[Degree]", "dates": "[Dates]"}]


def _parse_projects(section_lines: list[str]) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in section_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        is_bullet = stripped[0] in "-•"
        cleaned = stripped.lstrip("-• ").strip()
        if not cleaned:
            continue

        if not is_bullet and "|" in cleaned:
            if current:
                if not current["bullets"]:
                    current["bullets"].append("[To be filled: Project details]")
                projects.append(current)
            parts = [item.strip() for item in cleaned.split("|")]
            current = {
                "name": parts[0] if parts else "[Project]",
                "tech": parts[1] if len(parts) > 1 else "",
                "dates": parts[2] if len(parts) > 2 else "",
                "bullets": [],
            }
            continue

        if current is None:
            current = {"name": "[Project]", "tech": "", "dates": "", "bullets": []}

        current["bullets"].append(cleaned)

    if current:
        if not current["bullets"]:
            current["bullets"].append("[To be filled: Project details]")
        projects.append(current)

    return projects


def _parse_certifications(section_lines: list[str]) -> list[dict[str, str]]:
    return parse_pipe_delimited_items(
        section_lines, ("name", "issuer", "dates"), "[Certification]"
    )


def _parse_awards(section_lines: list[str]) -> list[dict[str, str]]:
    return parse_pipe_delimited_items(
        section_lines, ("name", "organization", "dates"), "[Award]"
    )


def normalize_resume_text_to_content(raw_text: str) -> dict[str, Any]:
    name, contact = _extract_header(raw_text)
    sections = _extract_sections(raw_text)

    return {
        "name": name,
        "contact": contact,
        "summary": " ".join(sections["summary"]).strip() or "[To be filled: Summary]",
        "skills": _parse_skills(sections["skills"]),
        "experience": _parse_experience(sections["experience"]),
        "education": _parse_education(sections["education"]),
        "projects": _parse_projects(sections["projects"]),
        "certifications": _parse_certifications(sections["certifications"]),
        "awards": _parse_awards(sections["awards"]),
    }


def init_cache_from_text(workspace: Path, raw_text: str) -> Path:
    return write_json_file(get_cache_path(workspace), normalize_resume_text_to_content(raw_text))


def update_cache_from_json(workspace: Path, payload: dict[str, Any]) -> Path:
    validate_resume_content(payload)
    return write_json_file(get_cache_path(workspace), payload)


def read_cache_json(workspace: Path) -> dict[str, Any]:
    return load_json_file(get_cache_path(workspace))


def init_base_template_from_text(workspace: Path, raw_text: str) -> Path:
    return write_json_file(get_base_template_path(workspace), normalize_resume_text_to_content(raw_text))


def init_working_from_template(workspace: Path) -> Path:
    return write_json_file(get_cache_path(workspace), load_json_file(get_base_template_path(workspace)))


def read_base_template_json(workspace: Path) -> dict[str, Any]:
    return load_json_file(get_base_template_path(workspace))


def has_base_template(workspace: Path) -> bool:
    return get_base_template_path(workspace).exists()


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _normalize_skill_set(skills: list[dict[str, Any]]) -> set[str]:
    return {
        f"{str(s.get('category', '')).strip()}: {str(s.get('items', '')).strip()}".strip()
        for s in skills
        if str(s.get("category", "")).strip() or str(s.get("items", "")).strip()
    }


def _normalize_items_text(items: list[dict[str, Any]], fields: list[str]) -> str:
    lines: list[str] = []
    for item in items:
        lines.append(" | ".join(str(item.get(f, "")).strip() for f in fields))
        for bullet in item.get("bullets", []):
            lines.append(str(bullet).strip())
    return _normalize_text("\n".join(lines))


def diff_cache_against_template(workspace: Path) -> dict[str, Any]:
    template = read_base_template_json(workspace)
    working = read_cache_json(workspace)

    def status(a: str, b: str) -> str:
        return "unchanged" if a == b else "modified"

    tmpl_skills = _normalize_skill_set(template.get("skills", []))
    work_skills = _normalize_skill_set(working.get("skills", []))

    return {
        "summary": {
            "status": status(
                _normalize_text(str(template.get("summary", ""))),
                _normalize_text(str(working.get("summary", ""))),
            ),
            "template": _normalize_text(str(template.get("summary", ""))),
            "working": _normalize_text(str(working.get("summary", ""))),
        },
        "skills": {
            "status": "unchanged" if tmpl_skills == work_skills else "modified",
            "added": sorted(work_skills - tmpl_skills),
            "removed": sorted(tmpl_skills - work_skills),
        },
        "experience": {
            "status": status(
                _normalize_items_text(template.get("experience", []), ["company", "title", "location", "dates"]),
                _normalize_items_text(working.get("experience", []), ["company", "title", "location", "dates"]),
            ),
            "bullet_count_template": sum(len(e.get("bullets", [])) for e in template.get("experience", [])),
            "bullet_count_working": sum(len(e.get("bullets", [])) for e in working.get("experience", [])),
        },
        "education": {
            "status": status(
                _normalize_items_text(template.get("education", []), ["school", "degree", "dates", "location"]),
                _normalize_items_text(working.get("education", []), ["school", "degree", "dates", "location"]),
            ),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage resume-working.json cache file"
    )
    parser.add_argument(
        "action",
        choices=[
            "reset", "init", "update", "show", "cleanup",
            "template-init", "template-use", "template-show", "template-check", "diff",
            "jd-save", "jd-show",
        ],
        help="Action to execute",
    )
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument(
        "--input",
        help="Input path (init/template-init uses raw text; update uses JSON)",
    )
    return parser.parse_args()


def _run_json_action(action: Callable[..., Any], *args: Any) -> int:
    try:
        print(json.dumps(action(*args), ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).expanduser().resolve()

    if args.action in {"init", "update", "template-init", "jd-save"} and not args.input:
        print("Error: init/update/template-init/jd-save requires --input parameter", file=sys.stderr)
        return 1

    if args.action in {"reset", "cleanup"}:
        removed = reset_cache_on_start(workspace)
        if args.action == "cleanup":
            print("Cache cleaned" if removed else "No cache to clean")
        else:
            print("Old cache removed" if removed else "No old cache found")
        return 0

    if args.action == "show":
        return _run_json_action(read_cache_json, workspace)

    if args.action == "diff":
        return _run_json_action(diff_cache_against_template, workspace)

    if args.action == "jd-show":
        return _run_json_action(read_jd_analysis, workspace)

    if args.action == "template-check":
        exists = has_base_template(workspace)
        if exists:
            print(f"Template exists: {get_base_template_path(workspace)}")
            return 0
        print("Template does not exist", file=sys.stderr)
        return 1

    if args.action == "template-show":
        return _run_json_action(read_base_template_json, workspace)

    if args.action == "template-use":
        try:
            path = init_working_from_template(workspace)
            print(f"Working cache initialized from template: {path}")
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    # Actions requiring --input file
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        if args.action == "jd-save":
            path = save_jd_analysis(workspace, load_json_file(input_path))
            print(f"JD analysis saved: {path}")
        elif args.action == "template-init":
            path = init_base_template_from_text(workspace, input_path.read_text(encoding="utf-8"))
            print(f"Template initialized: {path}")
        elif args.action == "init":
            path = init_cache_from_text(workspace, input_path.read_text(encoding="utf-8"))
            print(f"Cache initialized: {path}")
        else:  # update
            path = update_cache_from_json(workspace, load_json_file(input_path))
            print(f"Cache updated: {path}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
