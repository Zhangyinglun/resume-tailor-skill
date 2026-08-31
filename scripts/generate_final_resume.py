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

from scripts.audit_factual_integrity import audit_resume  # noqa: E402
from scripts.check_content_quality import run_all_checks  # noqa: E402
from scripts.check_pdf_quality import check_pdf_file  # noqa: E402
from scripts.layout_auto_tuner import (  # noqa: E402
    CONTENT_CHECKS,
    LAYOUT_FIXABLE_CHECKS,
    auto_fit_layout,
)
from scripts.resume_shared import load_json_file, validate_resume_content  # noqa: E402
from templates.layout_settings import LayoutSettings  # noqa: E402
from templates.modern_resume_template import archive_root_pdfs, generate_resume  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render final resume PDF (A4 single-page template) from JSON."
    )
    parser.add_argument("--input-json", required=True, help="Resume content JSON file path")
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output filename (filename only), example: 02_10_Name_Backend_Engineer_resume.pdf",
    )
    parser.add_argument(
        "--output-dir", default="resume_output", help="Output directory (default: resume_output)"
    )
    parser.add_argument(
        "--manifest-json",
        help="Tailoring Manifest path (default: resume-changes.json beside input)",
    )
    parser.add_argument(
        "--evidence-json",
        help="Candidate Evidence Ledger path (default: candidate-evidence.json beside input)",
    )
    parser.add_argument(
        "--base-json",
        help="Source Snapshot path (default: base-resume.json beside input)",
    )
    parser.add_argument(
        "--font-size-scale", type=float, default=None, help="Font size scale (0.7-1.3)"
    )
    parser.add_argument(
        "--line-height-scale", type=float, default=None, help="Line height scale (0.7-1.3)"
    )
    parser.add_argument(
        "--section-spacing-scale", type=float, default=None, help="Section spacing scale (0.7-1.3)"
    )
    parser.add_argument(
        "--item-spacing-scale", type=float, default=None, help="Item spacing scale (0.7-1.3)"
    )
    parser.add_argument(
        "--margin-top-mm", type=float, default=None, help="Top margin in mm (default: 5.0)"
    )
    parser.add_argument(
        "--margin-bottom-mm", type=float, default=None, help="Bottom margin in mm (default: 5.0)"
    )
    parser.add_argument(
        "--margin-side-inch",
        type=float,
        default=None,
        help="Left/right margin in inches (default: 0.6)",
    )
    parser.add_argument("--compact", action="store_true", help="Enable compact mode")
    parser.add_argument("--auto-fit", action="store_true", help="Auto-search layout parameters")
    parser.add_argument(
        "--auto-fit-max-trials", type=int, default=12, help="Max layout candidates (default: 12)"
    )
    return parser.parse_args()


def _build_layout(args: argparse.Namespace) -> LayoutSettings:
    """Build LayoutSettings from CLI args."""
    return LayoutSettings(
        font_size_scale=args.font_size_scale,
        line_height_scale=args.line_height_scale,
        section_spacing_scale=args.section_spacing_scale,
        item_spacing_scale=args.item_spacing_scale,
        margin_top_mm=args.margin_top_mm if args.margin_top_mm is not None else 5.0,
        margin_bottom_mm=(args.margin_bottom_mm if args.margin_bottom_mm is not None else 5.0),
        margin_side_inch=(args.margin_side_inch if args.margin_side_inch is not None else 0.6),
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

    if output_dir == PROJECT_ROOT or PROJECT_ROOT in output_dir.parents:
        print(
            "Error: Output must live in a workspace outside the Skill package.",
            file=sys.stderr,
        )
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
            print(
                f"Error: --{name.replace('_', '-')} must be between 0.7 and 1.3.", file=sys.stderr
            )
            return 1
    for name in ("margin_top_mm", "margin_bottom_mm", "margin_side_inch"):
        value = getattr(args, name)
        if value is not None and value <= 0:
            print(f"Error: --{name.replace('_', '-')} must be positive.", file=sys.stderr)
            return 1

    manifest_path = (
        Path(args.manifest_json).expanduser().resolve()
        if args.manifest_json
        else source_path.parent / "resume-changes.json"
    )
    evidence_path = (
        Path(args.evidence_json).expanduser().resolve()
        if args.evidence_json
        else source_path.parent / "candidate-evidence.json"
    )
    base_path = (
        Path(args.base_json).expanduser().resolve()
        if args.base_json
        else source_path.parent / "base-resume.json"
    )

    try:
        content = load_json_file(source_path)
        validate_resume_content(content, require_non_empty=True)
        manifest = load_json_file(manifest_path)
        audit_report = audit_resume(
            content,
            manifest,
            load_json_file(evidence_path),
            base_resume=load_json_file(base_path),
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: mandatory factual audit could not run: {exc}", file=sys.stderr)
        return 1
    if audit_report["verdict"] != "PASS":
        codes = ", ".join(sorted({finding["code"] for finding in audit_report["findings"]}))
        print(
            f"Error: mandatory factual audit failed: {codes}",
            file=sys.stderr,
        )
        return 1

    content_findings = [check for check in run_all_checks(content) if check["status"] != "PASS"]
    dispositions = {
        str(item.get("finding")): item
        for item in manifest.get("warning_dispositions", [])
        if isinstance(item, dict)
        and item.get("status") == "accepted"
        and str(item.get("reason", "")).strip()
    }
    unresolved_content = [
        finding for finding in content_findings if finding["name"] not in dispositions
    ]
    for finding in content_findings:
        resolution = dispositions.get(finding["name"])
        suffix = (
            f"; disposition: {resolution['reason']}" if resolution is not None else "; unresolved"
        )
        print(
            f"Content QA advisory [{finding['name']}]: {finding['detail']}{suffix}",
            file=sys.stderr,
        )
    if unresolved_content:
        print(
            "Error: unresolved content QA warnings block publication. "
            "Correct the text/evidence or add a reasoned warning disposition.",
            file=sys.stderr,
        )
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        if args.auto_fit:
            has_custom = any(
                getattr(args, attr) is not None
                for attr in (
                    "font_size_scale",
                    "line_height_scale",
                    "section_spacing_scale",
                    "item_spacing_scale",
                    "margin_top_mm",
                    "margin_bottom_mm",
                    "margin_side_inch",
                )
            )
            hint_layout = _build_layout(args) if has_custom or args.compact else None

            fit_result = auto_fit_layout(
                content,
                output_file=output_name,
                max_trials=args.auto_fit_max_trials,
                hint_layout=hint_layout,
            )
            layout = fit_result.best_layout
            failed_checks = [
                c.get("name")
                for c in fit_result.best_report.get("checks", [])
                if not c.get("passed")
            ]
            print(
                f"Auto-fit finished: trials={fit_result.trials_run}, "
                f"best_verdict={fit_result.best_report.get('verdict')}"
            )
            if failed_checks:
                layout_unresolved = [c for c in failed_checks if c in LAYOUT_FIXABLE_CHECKS]
                content_unresolved = [c for c in failed_checks if c in CONTENT_CHECKS]
                if layout_unresolved:
                    print(f"Auto-fit unresolved layout checks: {', '.join(layout_unresolved)}")
                if content_unresolved:
                    print(
                        f"Content issues (cannot fix by layout tuning): {', '.join(content_unresolved)}"
                    )
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
