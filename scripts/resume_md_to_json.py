#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将标准化简历 Markdown 转为模板输入 JSON。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _find_section(text: str, title: str) -> str:
    marker = f"## {title}"
    start = text.find(marker)
    if start < 0:
        return ""

    section_start = start + len(marker)
    next_start = text.find("\n## ", section_start)
    if next_start < 0:
        next_start = len(text)

    return text[section_start:next_start].strip()


def _parse_header(text: str) -> tuple[str, str]:
    name = "FULL NAME"
    contact = "City, State | Phone | Email | LinkedIn"

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Name:"):
            name = line.replace("Name:", "", 1).strip() or name
        elif line.startswith("Contact:"):
            contact = line.replace("Contact:", "", 1).strip() or contact

    return name, contact


def _parse_skills(section_text: str) -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        payload = stripped.lstrip("- ").strip()
        if ":" in payload:
            category, items = payload.split(":", 1)
            skills.append({"category": category.strip(), "items": items.strip()})
        elif payload:
            skills.append({"category": "Core", "items": payload})

    if not skills:
        skills.append({"category": "Core", "items": "[待补充技能]"})

    return skills


def _parse_experience(section_text: str) -> list[dict[str, object]]:
    experience: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("### "):
            if current:
                experience.append(current)

            header = stripped.replace("### ", "", 1).strip()
            parts = [item.strip() for item in header.split("|")]
            company = parts[0] if parts else "[Company]"
            title = parts[1] if len(parts) > 1 else "[Title]"
            location = parts[2] if len(parts) > 2 else "[Location]"
            dates = parts[3] if len(parts) > 3 else "[Dates]"

            current = {
                "company": company,
                "title": title,
                "location": location,
                "dates": dates,
                "bullets": [],
            }
            continue

        if stripped.startswith("-") and current is not None:
            bullet = stripped.lstrip("- ").strip()
            if bullet:
                current["bullets"].append(bullet)

    if current:
        experience.append(current)

    if not experience:
        experience.append(
            {
                "company": "[Company]",
                "title": "[Title]",
                "location": "[Location]",
                "dates": "[Dates]",
                "bullets": ["[待补充经历要点]"],
            }
        )

    for item in experience:
        if not item["bullets"]:
            item["bullets"] = ["[待补充经历要点]"]

    return experience


def _parse_education(section_text: str) -> list[dict[str, str]]:
    education: list[dict[str, str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue

        payload = stripped.lstrip("- ").strip()
        if not payload:
            continue

        parts = [item.strip() for item in payload.split("|")]
        school = parts[0] if parts else "[School]"
        degree = parts[1] if len(parts) > 1 else "[Degree]"
        dates = parts[2] if len(parts) > 2 else "[Dates]"

        education.append({"school": school, "degree": degree, "dates": dates})

    if not education:
        education.append({"school": "[School]", "degree": "[Degree]", "dates": "[Dates]"})

    return education


def markdown_to_content(markdown: str) -> dict[str, object]:
    name, contact = _parse_header(markdown)
    summary = _find_section(markdown, "SUMMARY") or "[待补充 Summary]"
    skills_text = _find_section(markdown, "TECHNICAL SKILLS")
    experience_text = _find_section(markdown, "PROFESSIONAL EXPERIENCE")
    education_text = _find_section(markdown, "EDUCATION")

    return {
        "name": name,
        "contact": contact,
        "summary": " ".join(summary.split()),
        "skills": _parse_skills(skills_text),
        "experience": _parse_experience(experience_text),
        "education": _parse_education(education_text),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把标准 Markdown 简历转换为 JSON")
    parser.add_argument("--input-md", required=True, help="输入 markdown 路径")
    parser.add_argument("--output-json", help="输出 JSON 路径；不传则打印到标准输出")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    input_path = Path(args.input_md).expanduser().resolve()

    if not input_path.exists():
        print(f"错误: 文件不存在: {input_path}")
        return 1

    markdown = input_path.read_text(encoding="utf-8")
    payload = markdown_to_content(markdown)

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"转换完成: {output_path}")
        return 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
