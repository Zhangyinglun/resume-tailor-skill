#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manage resume working cache (Markdown format)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CACHE_REL_PATH = Path("cache") / "resume-working.md"
BASE_TEMPLATE_REL_PATH = Path("cache") / "base-resume.md"


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


def reset_cache_on_start(workspace: Path) -> bool:
    cache_path = get_cache_path(workspace)
    if cache_path.exists():
        cache_path.unlink()
        return True
    return False


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


def normalize_resume_text_to_markdown(raw_text: str) -> str:
    name, contact = _extract_header(raw_text)
    sections = _extract_sections(raw_text)

    summary_text = " ".join(sections["summary"]).strip() or "[To be filled: Summary]"

    skill_lines = sections["skills"] or ["Core: [To be filled: Skills]"]
    normalized_skills = []
    for line in skill_lines:
        cleaned = line.lstrip("- ").strip()
        if ":" in cleaned:
            normalized_skills.append(cleaned)
        else:
            normalized_skills.append(f"Core: {cleaned}")

    experience_lines = sections["experience"]
    experience_block: list[str] = []
    if experience_lines:
        first = experience_lines[0].lstrip("- ").strip()
        experience_block.append(f"### {first}")
        bullets = [
            line.lstrip("- ").strip() for line in experience_lines[1:] if line.strip()
        ]
        if not bullets:
            bullets = ["[To be filled: Experience details]"]
        for bullet in bullets:
            experience_block.append(f"- {bullet}")
    else:
        experience_block.extend(
            [
                "### [Company | Title | Location | Dates]",
                "- [To be filled: Experience details]",
            ]
        )

    education_lines = sections["education"]
    normalized_education = [
        line.lstrip("- ").strip() for line in education_lines if line.strip()
    ]
    if not normalized_education:
        normalized_education = ["[School | Degree | Dates]"]

    lines: list[str] = [
        "# HEADER",
        f"Name: {name}",
        f"Contact: {contact}",
        "",
        "## SUMMARY",
        summary_text,
        "",
        "## TECHNICAL SKILLS",
    ]

    for item in normalized_skills:
        lines.append(f"- {item}")

    lines.extend(["", "## PROFESSIONAL EXPERIENCE"])
    lines.extend(experience_block)

    if sections["projects"]:
        lines.extend(["", "## PROJECTS"])
        first_project = sections["projects"][0].lstrip("- ").strip()
        lines.append(f"### {first_project}")
        for project_line in sections["projects"][1:]:
            cleaned = project_line.lstrip("- ").strip()
            if cleaned:
                lines.append(f"- {cleaned}")

    if sections["certifications"]:
        lines.extend(["", "## CERTIFICATIONS"])
        for certification in sections["certifications"]:
            cleaned = certification.lstrip("- ").strip()
            if cleaned:
                lines.append(f"- {cleaned}")

    if sections["awards"]:
        lines.extend(["", "## AWARDS"])
        for award in sections["awards"]:
            cleaned = award.lstrip("- ").strip()
            if cleaned:
                lines.append(f"- {cleaned}")

    lines.extend(["", "## EDUCATION"])

    for item in normalized_education:
        lines.append(f"- {item}")

    lines.append("")
    return "\n".join(lines)


def init_cache_from_text(workspace: Path, raw_text: str) -> Path:
    cache_path = get_cache_path(workspace)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = normalize_resume_text_to_markdown(raw_text)
    cache_path.write_text(markdown, encoding="utf-8")
    return cache_path


def update_cache_from_markdown(workspace: Path, markdown: str) -> Path:
    cache_path = get_cache_path(workspace)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(markdown.strip() + "\n", encoding="utf-8")
    return cache_path


def read_cache_markdown(workspace: Path) -> str:
    cache_path = get_cache_path(workspace)
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache does not exist: {cache_path}")
    return cache_path.read_text(encoding="utf-8")


def init_base_template_from_text(workspace: Path, raw_text: str) -> Path:
    """Initialize long-term template from raw resume text."""
    template_path = get_base_template_path(workspace)
    template_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = normalize_resume_text_to_markdown(raw_text)
    template_path.write_text(markdown, encoding="utf-8")
    return template_path


def init_working_from_template(workspace: Path) -> Path:
    """Initialize working cache from long-term template (will be overridden by subsequent subset selection)."""
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"Template does not exist: {template_path}")

    template_content = template_path.read_text(encoding="utf-8")
    cache_path = get_cache_path(workspace)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(template_content, encoding="utf-8")
    return cache_path


def read_base_template_markdown(workspace: Path) -> str:
    """Read long-term template content."""
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"Template does not exist: {template_path}")
    return template_path.read_text(encoding="utf-8")


def has_base_template(workspace: Path) -> bool:
    """Check if long-term template exists."""
    return get_base_template_path(workspace).exists()


def _extract_section_text(markdown: str, section_title: str) -> str:
    marker = f"## {section_title}"
    start = markdown.find(marker)
    if start < 0:
        return ""
    section_start = start + len(marker)
    next_start = markdown.find("\n## ", section_start)
    if next_start < 0:
        next_start = len(markdown)
    return markdown[section_start:next_start].strip()


def _count_bullets_in_experience(markdown: str) -> int:
    experience_text = _extract_section_text(markdown, "PROFESSIONAL EXPERIENCE")
    return sum(
        1 for line in experience_text.splitlines() if line.strip().startswith("-")
    )


def diff_cache_against_template(workspace: Path) -> dict[str, Any]:
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"Template does not exist: {template_path}")

    cache_path = get_cache_path(workspace)
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache does not exist: {cache_path}")

    template_markdown = template_path.read_text(encoding="utf-8")
    working_markdown = cache_path.read_text(encoding="utf-8")

    normalized_template = normalize_resume_text_to_markdown(template_markdown)

    summary_template = _extract_section_text(normalized_template, "SUMMARY")
    summary_working = _extract_section_text(working_markdown, "SUMMARY")
    skills_template = _extract_section_text(normalized_template, "TECHNICAL SKILLS")
    skills_working = _extract_section_text(working_markdown, "TECHNICAL SKILLS")
    experience_template = _extract_section_text(
        normalized_template, "PROFESSIONAL EXPERIENCE"
    )
    experience_working = _extract_section_text(
        working_markdown, "PROFESSIONAL EXPERIENCE"
    )
    education_template = _extract_section_text(normalized_template, "EDUCATION")
    education_working = _extract_section_text(working_markdown, "EDUCATION")

    template_skills = {
        line.strip()
        for line in skills_template.splitlines()
        if line.strip().startswith("-")
    }
    working_skills = {
        line.strip()
        for line in skills_working.splitlines()
        if line.strip().startswith("-")
    }

    return {
        "summary": {
            "status": "unchanged"
            if " ".join(summary_template.split()) == " ".join(summary_working.split())
            else "modified",
            "template": " ".join(summary_template.split()),
            "working": " ".join(summary_working.split()),
        },
        "skills": {
            "status": "unchanged" if template_skills == working_skills else "modified",
            "added": sorted(working_skills - template_skills),
            "removed": sorted(template_skills - working_skills),
        },
        "experience": {
            "status": "unchanged"
            if " ".join(experience_template.split())
            == " ".join(experience_working.split())
            else "modified",
            "bullet_count_template": _count_bullets_in_experience(normalized_template),
            "bullet_count_working": _count_bullets_in_experience(working_markdown),
        },
        "education": {
            "status": "unchanged"
            if " ".join(education_template.split())
            == " ".join(education_working.split())
            else "modified"
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage resume-working.md cache file")
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
        "--input", help="Input file path (init uses raw text, update uses markdown)"
    )
    return parser.parse_args()


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
            print(read_cache_markdown(workspace))
            return 0
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "diff":
        try:
            payload = diff_cache_against_template(workspace)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        except FileNotFoundError as exc:
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
            print(read_base_template_markdown(workspace))
            return 0
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "template-use":
        try:
            path = init_working_from_template(workspace)
            print(f"Working cache initialized from template: {path}")
            return 0
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "template-init":
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
            return 1

        payload = input_path.read_text(encoding="utf-8")
        path = init_base_template_from_text(workspace, payload)
        print(f"Template initialized: {path}")
        return 0

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    payload = input_path.read_text(encoding="utf-8")

    if args.action == "init":
        path = init_cache_from_text(workspace, payload)
        print(f"Cache initialized: {path}")
        return 0

    path = update_cache_from_markdown(workspace, payload)
    print(f"Cache updated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
