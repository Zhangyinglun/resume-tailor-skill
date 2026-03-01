#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate final resume PDF from JSON content."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from templates.modern_resume_template import generate_resume  # noqa: E402
from templates.layout_settings import LayoutSettings  # noqa: E402
from layout_auto_tuner import auto_fit_layout, LAYOUT_FIXABLE_CHECKS, CONTENT_CHECKS  # noqa: E402
from scripts.resume_shared import load_json_file, validate_resume_content  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render final resume PDF (A4 single-page template) from JSON."
    )
    parser.add_argument("--input-json", required=True, help="Resume content JSON file path")
    parser.add_argument(
        "--output-file", required=True,
        help="Output filename (filename only), example: 02_10_Name_Backend_Engineer_resume.pdf",
    )
    parser.add_argument("--output-dir", default="resume_output", help="Output directory (default: resume_output)")
    parser.add_argument("--font-size-scale", type=float, default=None, help="Font size scale (0.7-1.3)")
    parser.add_argument("--line-height-scale", type=float, default=None, help="Line height scale (0.7-1.3)")
    parser.add_argument("--section-spacing-scale", type=float, default=None, help="Section spacing scale (0.7-1.3)")
    parser.add_argument("--item-spacing-scale", type=float, default=None, help="Item spacing scale (0.7-1.3)")
    parser.add_argument("--margin-top-mm", type=float, default=5.0, help="Top margin in mm (default: 5.0)")
    parser.add_argument("--margin-bottom-mm", type=float, default=5.0, help="Bottom margin in mm (default: 5.0)")
    parser.add_argument("--margin-side-inch", type=float, default=0.6, help="Left/right margin in inches (default: 0.6)")
    parser.add_argument("--compact", action="store_true", help="Enable compact mode")
    parser.add_argument("--auto-fit", action="store_true", help="Auto-search layout parameters")
    parser.add_argument("--auto-fit-max-trials", type=int, default=12, help="Max layout candidates (default: 12)")
    return parser.parse_args()


def _build_layout(args: argparse.Namespace) -> LayoutSettings:
    """Build LayoutSettings from CLI args."""
    return LayoutSettings(
        font_size_scale=args.font_size_scale,
        line_height_scale=args.line_height_scale,
        section_spacing_scale=args.section_spacing_scale,
        item_spacing_scale=args.item_spacing_scale,
        margin_top_mm=args.margin_top_mm,
        margin_bottom_mm=args.margin_bottom_mm,
        margin_side_inch=args.margin_side_inch,
        compact_mode=args.compact,
    )


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()

    output_name = Path(args.output_file).name
    if output_name != args.output_file:
        print("Error: --output-file must contain filename only, no path.", file=sys.stderr)
        return 1

    source_path = Path(args.input_json).expanduser().resolve()
    if not source_path.exists():
        print(f"Error: Input file does not exist: {source_path}", file=sys.stderr)
        return 1

    if args.auto_fit_max_trials <= 0:
        print("Error: --auto-fit-max-trials must be positive.", file=sys.stderr)
        return 1

    try:
        content = load_json_file(source_path)
        validate_resume_content(content, require_non_empty=True)

        if args.auto_fit:
            has_custom = any(
                getattr(args, attr) is not None
                for attr in ("font_size_scale", "line_height_scale",
                              "section_spacing_scale", "item_spacing_scale")
            )
            hint_layout = _build_layout(args) if has_custom or args.compact else None

            fit_result = auto_fit_layout(
                content, output_file=output_name,
                max_trials=args.auto_fit_max_trials, hint_layout=hint_layout,
            )
            layout = fit_result.best_layout
            failed_checks = [
                c.get("name") for c in fit_result.best_report.get("checks", [])
                if c.get("passed") is False
            ]
            print(f"Auto-fit finished: trials={fit_result.trials_run}, "
                  f"best_verdict={fit_result.best_report.get('verdict')}")
            if failed_checks:
                layout_unresolved = [c for c in failed_checks if c in LAYOUT_FIXABLE_CHECKS]
                content_unresolved = [c for c in failed_checks if c in CONTENT_CHECKS]
                if layout_unresolved:
                    print(f"Auto-fit unresolved layout checks: {', '.join(layout_unresolved)}")
                if content_unresolved:
                    print(f"Content issues (cannot fix by layout tuning): {', '.join(content_unresolved)}")
        else:
            layout = _build_layout(args)

        output_path = generate_resume(
            output_name, content, base_dir=str(output_dir), layout=layout
        )
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Generated successfully: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
