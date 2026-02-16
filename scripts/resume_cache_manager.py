#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管理简历工作缓存（Markdown）。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

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
    }

    current_section = "summary"
    for line in lines:
        if not line:
            continue
        maybe_section = _normalize_heading(line)
        if maybe_section:
            current_section = maybe_section
            continue
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

    summary_text = " ".join(sections["summary"]).strip() or "[待补充 Summary]"

    skill_lines = sections["skills"] or ["Core: [待补充技能]"]
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
            bullets = ["[待补充经历要点]"]
        for bullet in bullets:
            experience_block.append(f"- {bullet}")
    else:
        experience_block.extend(
            ["### [Company | Title | Location | Dates]", "- [待补充经历要点]"]
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
        raise FileNotFoundError(f"缓存不存在: {cache_path}")
    return cache_path.read_text(encoding="utf-8")


def init_base_template_from_text(workspace: Path, raw_text: str) -> Path:
    """从原始简历文本初始化长期模板。"""
    template_path = get_base_template_path(workspace)
    template_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = normalize_resume_text_to_markdown(raw_text)
    template_path.write_text(markdown, encoding="utf-8")
    return template_path


def init_working_from_template(workspace: Path) -> Path:
    """从长期模板初始化工作缓存（会被后续子集选择覆盖）。"""
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_path}")

    template_content = template_path.read_text(encoding="utf-8")
    cache_path = get_cache_path(workspace)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(template_content, encoding="utf-8")
    return cache_path


def read_base_template_markdown(workspace: Path) -> str:
    """读取长期模板内容。"""
    template_path = get_base_template_path(workspace)
    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_path}")
    return template_path.read_text(encoding="utf-8")


def has_base_template(workspace: Path) -> bool:
    """检查是否存在长期模板。"""
    return get_base_template_path(workspace).exists()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="管理 resume-working.md 缓存文件")
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
        ],
        help="执行动作",
    )
    parser.add_argument("--workspace", default=".", help="工作区根目录")
    parser.add_argument(
        "--input", help="输入文件路径（init 使用原始文本，update 使用 markdown）"
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).expanduser().resolve()

    if args.action in {"init", "update", "template-init"} and not args.input:
        print("错误: init/update/template-init 需要 --input 参数", file=sys.stderr)
        return 1

    if args.action == "reset":
        removed = reset_cache_on_start(workspace)
        print("已删除旧缓存" if removed else "无旧缓存")
        return 0

    if args.action == "cleanup":
        removed = cleanup_cache(workspace)
        print("已清理缓存" if removed else "无缓存可清理")
        return 0

    if args.action == "show":
        try:
            print(read_cache_markdown(workspace))
            return 0
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "template-check":
        exists = has_base_template(workspace)
        if exists:
            print(f"模板存在: {get_base_template_path(workspace)}")
            return 0
        print("模板不存在", file=sys.stderr)
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
            print(f"已从模板初始化工作缓存: {path}")
            return 0
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.action == "template-init":
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            print(f"错误: 输入文件不存在: {input_path}", file=sys.stderr)
            return 1

        payload = input_path.read_text(encoding="utf-8")
        path = init_base_template_from_text(workspace, payload)
        print(f"模板已初始化: {path}")
        return 0

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}", file=sys.stderr)
        return 1

    payload = input_path.read_text(encoding="utf-8")

    if args.action == "init":
        path = init_cache_from_text(workspace, payload)
        print(f"缓存已初始化: {path}")
        return 0

    path = update_cache_from_markdown(workspace, payload)
    print(f"缓存已更新: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
