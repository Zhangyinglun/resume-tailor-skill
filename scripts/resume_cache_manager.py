#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manage resume cache and template files (JSON format)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CACHE_REL_PATH = Path("cache") / "resume-working.json"
BASE_TEMPLATE_REL_PATH = Path("cache") / "base-resume.json"
LEGACY_CACHE_REL_PATH = Path("cache") / "resume-working.md"
LEGACY_BASE_TEMPLATE_REL_PATH = Path("cache") / "base-resume.md"


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


def _get_legacy_cache_path(workspace: Path) -> Path:
    return workspace / LEGACY_CACHE_REL_PATH


def _get_legacy_base_template_path(workspace: Path) -> Path:
    return workspace / LEGACY_BASE_TEMPLATE_REL_PATH


def reset_cache_on_start(workspace: Path) -> bool:
    removed = False
    for path in (get_cache_path(workspace), _get_legacy_cache_path(workspace)):
        if path.exists():
            path.unlink()
            removed = True
    return removed


def cleanup_cache(workspace: Path) -> bool:
    return reset_cache_on_start(workspace)


def _normalize_heading(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z\s]", "", text).strip().lower()
    return SECTION_ALIASES.get(normalized, "")


def _extract_sections(raw_text: str) -> dict[str, list[str]]:
    lines = [line.strip() for line in raw_text.splitlines()]
    sections: dict[str, list[str]] = {
        "summary": [],
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "awards": [],
    }

    current_section = ""
    for line in lines:
        if not line:
            continue
        maybe_section = _normalize_heading(line)
        if maybe_section:
            current_section = maybe_section
            continue
        if current_section:
            sections[current_section].append(line)

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

    if not skills:
        skills.append({"category": "Core", "items": "[To be filled: Skills]"})

    return skills


def _split_tab_or_multi_space(value: str) -> list[str]:
    cleaned = value.strip()
    if not cleaned:
        return []
    if "\t" in cleaned:
        return [part.strip() for part in cleaned.split("\t") if part.strip()]
    if re.search(r"\s{2,}", cleaned):
        return [part.strip() for part in re.split(r"\s{2,}", cleaned) if part.strip()]
    return [cleaned]


def _split_title_location(value: str) -> tuple[str, str]:
    parts = _split_tab_or_multi_space(value)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return value.strip() or "[Title]", "[Location]"


def _split_degree_dates(value: str) -> tuple[str, str]:
    parts = _split_tab_or_multi_space(value)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return value.strip() or "[Degree]", "[Dates]"


def _parse_experience(section_lines: list[str]) -> list[dict[str, Any]]:
    experience: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in section_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        is_bullet = stripped.startswith("-") or stripped.startswith("•")
        cleaned = stripped.lstrip("-• ").strip()
        if not cleaned:
            continue

        if not is_bullet and "|" in cleaned:
            if current:
                if not current["bullets"]:
                    current["bullets"].append("[To be filled: Experience details]")
                experience.append(current)

            parts = [item.strip() for item in cleaned.split("|")]
            title = "[Title]"
            location = "[Location]"
            dates = "[Dates]"

            if len(parts) > 3:
                title = parts[1]
                location = parts[2]
                dates = parts[3]
            elif len(parts) == 3:
                title, location = _split_title_location(parts[1])
                dates = parts[2]
            elif len(parts) == 2:
                title = parts[1]

            current = {
                "company": parts[0] if parts else "[Company]",
                "title": title,
                "location": location,
                "dates": dates,
                "bullets": [],
            }
            continue

        if current is None:
            current = {
                "company": "[Company]",
                "title": "[Title]",
                "location": "[Location]",
                "dates": "[Dates]",
                "bullets": [],
            }

        current["bullets"].append(cleaned)

    if current:
        if not current["bullets"]:
            current["bullets"].append("[To be filled: Experience details]")
        experience.append(current)

    if not experience:
        experience.append(
            {
                "company": "[Company]",
                "title": "[Title]",
                "location": "[Location]",
                "dates": "[Dates]",
                "bullets": ["[To be filled: Experience details]"],
            }
        )

    return experience


def _parse_education(section_lines: list[str]) -> list[dict[str, str]]:
    education: list[dict[str, str]] = []
    for line in section_lines:
        cleaned = line.lstrip("-• ").strip()
        if not cleaned or "|" not in cleaned:
            continue
        parts = [item.strip() for item in cleaned.split("|")]

        degree = "[Degree]"
        dates = "[Dates]"
        if len(parts) > 2:
            degree = parts[1]
            dates = parts[2]
        elif len(parts) == 2:
            degree, dates = _split_degree_dates(parts[1])

        education.append(
            {
                "school": parts[0] if parts else "[School]",
                "degree": degree,
                "dates": dates,
            }
        )

    if not education:
        education.append(
            {"school": "[School]", "degree": "[Degree]", "dates": "[Dates]"}
        )

    return education


def _parse_projects(section_lines: list[str]) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in section_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        is_bullet = stripped.startswith("-") or stripped.startswith("•")
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
    certifications: list[dict[str, str]] = []
    for line in section_lines:
        cleaned = line.lstrip("-• ").strip()
        if not cleaned:
            continue
        parts = [item.strip() for item in cleaned.split("|")]
        certifications.append(
            {
                "name": parts[0] if parts else "[Certification]",
                "issuer": parts[1] if len(parts) > 1 else "",
                "dates": parts[2] if len(parts) > 2 else "",
            }
        )
    return certifications


def _parse_awards(section_lines: list[str]) -> list[dict[str, str]]:
    awards: list[dict[str, str]] = []
    for line in section_lines:
        cleaned = line.lstrip("-• ").strip()
        if not cleaned:
            continue
        parts = [item.strip() for item in cleaned.split("|")]
        awards.append(
            {
                "name": parts[0] if parts else "[Award]",
                "organization": parts[1] if len(parts) > 1 else "",
                "dates": parts[2] if len(parts) > 2 else "",
            }
        )
    return awards


def normalize_resume_text_to_content(raw_text: str) -> dict[str, Any]:
    name, contact = _extract_header(raw_text)
    sections = _extract_sections(raw_text)

    summary = " ".join(sections["summary"]).strip() or "[To be filled: Summary]"

    return {
        "name": name,
        "contact": contact,
        "summary": summary,
        "skills": _parse_skills(sections["skills"]),
        "experience": _parse_experience(sections["experience"]),
        "education": _parse_education(sections["education"]),
        "projects": _parse_projects(sections["projects"]),
        "certifications": _parse_certifications(sections["certifications"]),
        "awards": _parse_awards(sections["awards"]),
    }


def _validate_json_content(payload: dict[str, Any]) -> None:
    required = ("name", "contact", "summary", "skills", "experience", "education")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Input JSON missing required fields: {', '.join(missing)}")

    if not isinstance(payload["skills"], list):
        raise ValueError("`skills` must be an array.")
    if not isinstance(payload["experience"], list):
        raise ValueError("`experience` must be an array.")
    if not isinstance(payload["education"], list):
        raise ValueError("`education` must be an array.")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def init_cache_from_text(workspace: Path, raw_text: str) -> Path:
    cache_path = get_cache_path(workspace)
    payload = normalize_resume_text_to_content(raw_text)
    return _write_json(cache_path, payload)


def update_cache_from_json(workspace: Path, payload: dict[str, Any]) -> Path:
    _validate_json_content(payload)
    cache_path = get_cache_path(workspace)
    return _write_json(cache_path, payload)


def read_cache_json(workspace: Path) -> dict[str, Any]:
    cache_path = get_cache_path(workspace)
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache does not exist: {cache_path}")

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Cache JSON must be an object: {cache_path}")
    return payload


def init_base_template_from_text(workspace: Path, raw_text: str) -> Path:
    template_path = get_base_template_path(workspace)
    payload = normalize_resume_text_to_content(raw_text)
    return _write_json(template_path, payload)


def init_working_from_template(workspace: Path) -> Path:
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"Template does not exist: {template_path}")

    payload = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Template JSON must be an object: {template_path}")

    return _write_json(get_cache_path(workspace), payload)


def read_base_template_json(workspace: Path) -> dict[str, Any]:
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"Template does not exist: {template_path}")

    payload = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Template JSON must be an object: {template_path}")
    return payload


def has_base_template(workspace: Path) -> bool:
    return get_base_template_path(workspace).exists()


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _normalize_skill_set(skills: list[dict[str, Any]]) -> set[str]:
    normalized: set[str] = set()
    for skill in skills:
        category = str(skill.get("category", "")).strip()
        items = str(skill.get("items", "")).strip()
        if category or items:
            normalized.add(f"{category}: {items}".strip())
    return normalized


def _normalize_experience_text(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in items:
        lines.append(
            " | ".join(
                [
                    str(item.get("company", "")).strip(),
                    str(item.get("title", "")).strip(),
                    str(item.get("location", "")).strip(),
                    str(item.get("dates", "")).strip(),
                ]
            )
        )
        for bullet in item.get("bullets", []):
            lines.append(str(bullet).strip())
    return _normalize_text("\n".join(lines))


def _normalize_education_text(items: list[dict[str, Any]]) -> str:
    lines = [
        " | ".join(
            [
                str(item.get("school", "")).strip(),
                str(item.get("degree", "")).strip(),
                str(item.get("dates", "")).strip(),
            ]
        )
        for item in items
    ]
    return _normalize_text("\n".join(lines))


def _count_bullets_in_experience(items: list[dict[str, Any]]) -> int:
    return sum(len(item.get("bullets", [])) for item in items)


def diff_cache_against_template(workspace: Path) -> dict[str, Any]:
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"Template does not exist: {template_path}")

    cache_path = get_cache_path(workspace)
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache does not exist: {cache_path}")

    template_payload = read_base_template_json(workspace)
    working_payload = read_cache_json(workspace)

    summary_template = str(template_payload.get("summary", ""))
    summary_working = str(working_payload.get("summary", ""))
    skills_template = template_payload.get("skills", [])
    skills_working = working_payload.get("skills", [])
    experience_template = template_payload.get("experience", [])
    experience_working = working_payload.get("experience", [])
    education_template = template_payload.get("education", [])
    education_working = working_payload.get("education", [])

    template_skills = _normalize_skill_set(skills_template)
    working_skills = _normalize_skill_set(skills_working)

    return {
        "summary": {
            "status": "unchanged"
            if _normalize_text(summary_template) == _normalize_text(summary_working)
            else "modified",
            "template": _normalize_text(summary_template),
            "working": _normalize_text(summary_working),
        },
        "skills": {
            "status": "unchanged" if template_skills == working_skills else "modified",
            "added": sorted(working_skills - template_skills),
            "removed": sorted(template_skills - working_skills),
        },
        "experience": {
            "status": "unchanged"
            if _normalize_experience_text(experience_template)
            == _normalize_experience_text(experience_working)
            else "modified",
            "bullet_count_template": _count_bullets_in_experience(experience_template),
            "bullet_count_working": _count_bullets_in_experience(experience_working),
        },
        "education": {
            "status": "unchanged"
            if _normalize_education_text(education_template)
            == _normalize_education_text(education_working)
            else "modified"
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage resume-working.json cache file"
    )
    parser.add_argument(
        "action",
        choices=[
            "reset",
            "init",
            "update",
            "show",
            "cleanup",
            "template-init",
            "template-use",
            "template-show",
            "template-check",
            "diff",
        ],
        help="Action to execute",
    )
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument(
        "--input",
        help="Input path (init/template-init uses raw text; update uses JSON)",
    )
    return parser.parse_args()


def _load_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Input JSON must be an object: {path}")
    return payload


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).expanduser().resolve()

    if args.action in {"init", "update", "template-init"} and not args.input:
        print(
            "Error: init/update/template-init requires --input parameter",
            file=sys.stderr,
        )
        return 1

    if args.action == "reset":
        removed = reset_cache_on_start(workspace)
        print("Old cache removed" if removed else "No old cache found")
        return 0

    if args.action == "cleanup":
        removed = cleanup_cache(workspace)
        print("Cache cleaned" if removed else "No cache to clean")
        return 0

    if args.action == "show":
        try:
            print(json.dumps(read_cache_json(workspace), ensure_ascii=False, indent=2))
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "diff":
        try:
            payload = diff_cache_against_template(workspace)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "template-check":
        exists = has_base_template(workspace)
        if exists:
            print(f"Template exists: {get_base_template_path(workspace)}")
            return 0
        print("Template does not exist", file=sys.stderr)
        return 1

    if args.action == "template-show":
        try:
            print(
                json.dumps(
                    read_base_template_json(workspace), ensure_ascii=False, indent=2
                )
            )
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "template-use":
        try:
            path = init_working_from_template(workspace)
            print(f"Working cache initialized from template: {path}")
            return 0
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        if args.action == "template-init":
            raw_text = input_path.read_text(encoding="utf-8")
            path = init_base_template_from_text(workspace, raw_text)
            print(f"Template initialized: {path}")
            return 0

        if args.action == "init":
            raw_text = input_path.read_text(encoding="utf-8")
            path = init_cache_from_text(workspace, raw_text)
            print(f"Cache initialized: {path}")
            return 0

        payload = _load_json_file(input_path)
        path = update_cache_from_json(workspace, payload)
        print(f"Cache updated: {path}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
