#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate final resume PDF from JSON or Markdown content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from templates.modern_resume_template import generate_resume  # noqa: E402
from resume_md_to_json import markdown_to_content  # noqa: E402

REQUIRED_KEYS = ("name", "contact", "summary", "skills", "experience", "education")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render final resume PDF (A4 single-page template) from JSON or standardized Markdown."
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input-json", help="Resume content JSON file path")
    source_group.add_argument(
        "--input-md", help="Standardized resume Markdown file path"
    )

    parser.add_argument(
        "--output-file",
        required=True,
        help="Output filename (filename only), example: 02_10_Name_Backend_Engineer_resume.pdf",
    )
    parser.add_argument(
        "--output-dir",
        default="resume_output",
        help="Output directory (default: resume_output)",
    )
    return parser.parse_args()


def load_json_content(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Input JSON must have a dictionary at the top level.")

    return data


def load_markdown_content(input_path: Path) -> dict[str, Any]:
    markdown = input_path.read_text(encoding="utf-8")
    return markdown_to_content(markdown)


def validate_content(content: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in content]
    if missing:
        raise ValueError(f"Input content missing required fields: {', '.join(missing)}")

    if not isinstance(content["skills"], list) or not content["skills"]:
        raise ValueError("`skills` must be a non-empty array.")
    if not isinstance(content["experience"], list) or not content["experience"]:
        raise ValueError("`experience` must be a non-empty array.")
    if not isinstance(content["education"], list) or not content["education"]:
        raise ValueError("`education` must be a non-empty array.")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()

    output_name = Path(args.output_file).name
    if output_name != args.output_file:
        print(
            "Error: --output-file must contain filename only, no path.", file=sys.stderr
        )
        return 1

    source_path = Path(args.input_json or args.input_md).expanduser().resolve()
    if not source_path.exists():
        print(f"Error: Input file does not exist: {source_path}", file=sys.stderr)
        return 1

    try:
        if args.input_json:
            content = load_json_content(source_path)
        else:
            content = load_markdown_content(source_path)

        validate_content(content)
        output_path = generate_resume(output_name, content, base_dir=str(output_dir))
    except Exception as exc:  # noqa: BLE001
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Generated successfully: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
