#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate final resume PDF from JSON content."""

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
from templates.layout_settings import LayoutSettings  # noqa: E402
from layout_auto_tuner import auto_fit_layout  # noqa: E402

REQUIRED_KEYS = ("name", "contact", "summary", "skills", "experience", "education")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render final resume PDF (A4 single-page template) from JSON."
    )
    parser.add_argument(
        "--input-json", required=True, help="Resume content JSON file path"
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
    parser.add_argument(
        "--font-size-scale",
        type=float,
        default=None,
        help="Font size scale factor (0.7-1.3, default: 1.0)",
    )
    parser.add_argument(
        "--line-height-scale",
        type=float,
        default=None,
        help="Line height scale factor (0.7-1.3, default: 1.0)",
    )
    parser.add_argument(
        "--section-spacing-scale",
        type=float,
        default=None,
        help="Section spacing scale factor (0.7-1.3, default: 1.0)",
    )
    parser.add_argument(
        "--item-spacing-scale",
        type=float,
        default=None,
        help="Item spacing scale factor (0.7-1.3, default: 1.0)",
    )
    parser.add_argument(
        "--margin-top-mm",
        type=float,
        default=5.0,
        help="Top margin in mm (default: 5.0)",
    )
    parser.add_argument(
        "--margin-bottom-mm",
        type=float,
        default=5.0,
        help="Bottom margin in mm (default: 5.0)",
    )
    parser.add_argument(
        "--margin-side-inch",
        type=float,
        default=0.6,
        help="Left/right margin in inches (default: 0.6)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Enable compact mode (reduces spacing and font sizes)",
    )
    parser.add_argument(
        "--auto-fit",
        action="store_true",
        help="Auto-search layout parameters to maximize PDF quality checks",
    )
    parser.add_argument(
        "--auto-fit-max-trials",
        type=int,
        default=12,
        help="Maximum layout candidates to try in auto-fit mode (default: 12)",
    )
    return parser.parse_args()


def load_json_content(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Input JSON must have a dictionary at the top level.")

    return data


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

    source_path = Path(args.input_json).expanduser().resolve()
    if not source_path.exists():
        print(f"Error: Input file does not exist: {source_path}", file=sys.stderr)
        return 1

    if args.auto_fit_max_trials <= 0:
        print("Error: --auto-fit-max-trials must be positive.", file=sys.stderr)
        return 1

    try:
        content = load_json_content(source_path)
        validate_content(content)

        if args.auto_fit:
            fit_result = auto_fit_layout(
                content,
                output_file=output_name,
                max_trials=args.auto_fit_max_trials,
            )
            layout = fit_result.best_layout
            failed_checks = [
                check.get("name")
                for check in fit_result.best_report.get("checks", [])
                if check.get("passed") is False
            ]
            print(
                f"Auto-fit finished: trials={fit_result.trials_run}, "
                f"best_verdict={fit_result.best_report.get('verdict')}"
            )
            if failed_checks:
                print(f"Auto-fit unresolved checks: {', '.join(failed_checks)}")
        else:
            layout = LayoutSettings(
                font_size_scale=args.font_size_scale,
                line_height_scale=args.line_height_scale,
                section_spacing_scale=args.section_spacing_scale,
                item_spacing_scale=args.item_spacing_scale,
                margin_top_mm=args.margin_top_mm,
                margin_bottom_mm=args.margin_bottom_mm,
                margin_side_inch=args.margin_side_inch,
                compact_mode=args.compact,
            )

        output_path = generate_resume(
            output_name, content, base_dir=str(output_dir), layout=layout
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Generated successfully: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
