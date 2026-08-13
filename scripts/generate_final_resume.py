#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate final resume PDF from JSON content."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from templates.modern_resume_template import archive_root_pdfs, generate_resume  # noqa: E402
from templates.layout_settings import LayoutSettings  # noqa: E402
from scripts.layout_auto_tuner import auto_fit_layout, LAYOUT_FIXABLE_CHECKS, CONTENT_CHECKS  # noqa: E402
from scripts.check_pdf_quality import check_pdf_file  # noqa: E402
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
    parser.add_argument("--margin-top-mm", type=float, default=None, help="Top margin in mm (default: 5.0)")
    parser.add_argument("--margin-bottom-mm", type=float, default=None, help="Bottom margin in mm (default: 5.0)")
    parser.add_argument("--margin-side-inch", type=float, default=None, help="Left/right margin in inches (default: 0.6)")
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
        margin_top_mm=args.margin_top_mm if args.margin_top_mm is not None else 5.0,
        margin_bottom_mm=(
            args.margin_bottom_mm if args.margin_bottom_mm is not None else 5.0
        ),
        margin_side_inch=(
            args.margin_side_inch if args.margin_side_inch is not None else 0.6
        ),
        compact_mode=args.compact,
    )


def _next_rejected_path(output_dir: Path, output_name: str) -> Path:
    """Return a non-conflicting path for a generated PDF that failed QA."""
    rejected_dir = output_dir / "rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(output_name).stem
    candidate = rejected_dir / f"{stem}_rejected.pdf"
    sequence = 2
    while candidate.exists():
        candidate = rejected_dir / f"{stem}_rejected_{sequence}.pdf"
        sequence += 1
    return candidate


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()

    output_name = Path(args.output_file).name
    if output_name != args.output_file:
        print("Error: --output-file must contain filename only, no path.", file=sys.stderr)
        return 1
    if Path(output_name).suffix.casefold() != ".pdf":
        print("Error: --output-file must use a .pdf extension.", file=sys.stderr)
        return 1

    source_path = Path(args.input_json).expanduser().resolve()
    if not source_path.exists():
        print(f"Error: Input file does not exist: {source_path}", file=sys.stderr)
        return 1

    if args.auto_fit_max_trials <= 0:
        print("Error: --auto-fit-max-trials must be positive.", file=sys.stderr)
        return 1
    for name in (
        "font_size_scale",
        "line_height_scale",
        "section_spacing_scale",
        "item_spacing_scale",
    ):
        value = getattr(args, name)
        if value is not None and not 0.7 <= value <= 1.3:
            print(f"Error: --{name.replace('_', '-')} must be between 0.7 and 1.3.", file=sys.stderr)
            return 1
    for name in ("margin_top_mm", "margin_bottom_mm", "margin_side_inch"):
        value = getattr(args, name)
        if value is not None and value <= 0:
            print(f"Error: --{name.replace('_', '-')} must be positive.", file=sys.stderr)
            return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        content = load_json_file(source_path)
        validate_resume_content(content, require_non_empty=True)

        if args.auto_fit:
            has_custom = any(
                getattr(args, attr) is not None
                for attr in ("font_size_scale", "line_height_scale",
                              "section_spacing_scale", "item_spacing_scale",
                              "margin_top_mm", "margin_bottom_mm",
                              "margin_side_inch")
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

        with tempfile.TemporaryDirectory(
            prefix=".resume-staging-", dir=str(output_dir)
        ) as staging_dir:
            candidate_path = Path(
                generate_resume(
                    output_name,
                    content,
                    base_dir=staging_dir,
                    layout=layout,
                )
            )
            qa_report = check_pdf_file(candidate_path)
            qa_passed = qa_report.get("verdict") == "PASS"

            if not qa_passed:
                failed = [
                    check["name"]
                    for check in qa_report.get("checks", [])
                    if not check.get("passed")
                ]
                rejected_path = _next_rejected_path(output_dir, output_name)
                candidate_path.replace(rejected_path)
                print(
                    f"\u2717 QA not passed ({', '.join(failed)}); "
                    "previous resume files were preserved."
                )
                print(f"Rejected candidate retained for review: {rejected_path}")
                return 2

            archive_root_pdfs(output_dir)
            final_path = output_dir / output_name
            candidate_path.replace(final_path)
    except Exception as exc:  # noqa: BLE001 - CLI must convert renderer/parser errors into a stable exit code.
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1

    print("\u2713 QA passed; previous version(s) archived to backup/")
    print(f"Generated successfully: {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
