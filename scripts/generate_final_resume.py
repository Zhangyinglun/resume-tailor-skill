#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 JSON 或 Markdown 内容生成最终简历 PDF。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"
if str(TEMPLATE_DIR) not in sys.path:
    sys.path.insert(0, str(TEMPLATE_DIR))

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from modern_resume_template import generate_resume  # noqa: E402
from resume_md_to_json import markdown_to_content  # noqa: E402

REQUIRED_KEYS = ("name", "contact", "summary", "skills", "experience", "education")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="根据 JSON 或标准化 Markdown 渲染最终简历 PDF（A4 单页模板）。"
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input-json", help="简历内容 JSON 文件路径")
    source_group.add_argument("--input-md", help="标准化简历 Markdown 文件路径")

    parser.add_argument(
        "--output-file",
        required=True,
        help="输出文件名（仅文件名），示例：02_10_Name_Backend_Engineer_resume.pdf",
    )
    parser.add_argument(
        "--output-dir",
        default="resume_output",
        help="输出目录（默认：resume_output）",
    )
    return parser.parse_args()


def load_json_content(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("输入 JSON 的顶层必须是对象。")

    return data


def load_markdown_content(input_path: Path) -> dict[str, Any]:
    markdown = input_path.read_text(encoding="utf-8")
    return markdown_to_content(markdown)


def validate_content(content: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in content]
    if missing:
        raise ValueError(f"输入内容缺少必填字段: {', '.join(missing)}")

    if not isinstance(content["skills"], list) or not content["skills"]:
        raise ValueError("`skills` 必须是非空数组。")
    if not isinstance(content["experience"], list) or not content["experience"]:
        raise ValueError("`experience` 必须是非空数组。")
    if not isinstance(content["education"], list) or not content["education"]:
        raise ValueError("`education` 必须是非空数组。")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()

    output_name = Path(args.output_file).name
    if output_name != args.output_file:
        print("错误: --output-file 必须仅包含文件名，不可包含路径。", file=sys.stderr)
        return 1

    source_path = Path(args.input_json or args.input_md).expanduser().resolve()
    if not source_path.exists():
        print(f"错误: 输入文件不存在: {source_path}", file=sys.stderr)
        return 1

    try:
        if args.input_json:
            content = load_json_content(source_path)
        else:
            content = load_markdown_content(source_path)

        validate_content(content)
        output_path = generate_resume(output_name, content, base_dir=str(output_dir))
    except Exception as exc:  # noqa: BLE001
        print(f"生成失败: {exc}", file=sys.stderr)
        return 1

    print(f"生成成功: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
