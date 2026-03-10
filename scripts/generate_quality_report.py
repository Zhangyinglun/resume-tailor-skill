#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a quality check report for a tailored resume.

Outputs Markdown to stdout — no files are written.

Usage:
    python3 scripts/generate_quality_report.py \
        --resume cache/resume-working.json \
        --jd-analysis cache/jd-analysis.json \
        [--pdf resume_output/resume.pdf]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from scripts.check_content_quality import run_all_checks
from scripts.resume_shared import extract_terms, load_json_file

_SNIPPET_LEN = 80


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _collect_searchable_texts(resume: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (location, text) pairs covering summary, skills, bullets."""
    texts: list[tuple[str, str]] = []

    summary = resume.get("summary", "")
    if summary:
        texts.append(("summary", summary))

    for i, sk in enumerate(resume.get("skills", [])):
        items = sk.get("items", "")
        if items:
            texts.append((f"skills[{i}].items", items))

    for i, exp in enumerate(resume.get("experience", [])):
        for j, bullet in enumerate(exp.get("bullets", [])):
            texts.append((f"experience[{i}].bullets[{j}]", str(bullet)))

    for i, proj in enumerate(resume.get("projects", [])):
        for j, bullet in enumerate(proj.get("bullets", [])):
            texts.append((f"projects[{i}].bullets[{j}]", str(bullet)))

    return texts


def build_keyword_coverage(
    resume: dict[str, Any],
    jd_analysis: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build keyword → coverage matrix for P1/P2/P3 tiers.

    Returns:
        {
          "P1": [{"keyword": str, "covered": bool, "location": str}, ...],
          "P2": [...],
          "P3": [...],
        }
    """
    keywords = jd_analysis.get("keywords", {})
    texts = _collect_searchable_texts(resume)

    # Pre-compute lowercase once — avoids repeated .lower() per keyword
    texts_lower = [(loc, text.lower(), text) for loc, text in texts]

    result: dict[str, list[dict[str, Any]]] = {"P1": [], "P2": [], "P3": []}
    for tier in ("P1", "P2", "P3"):
        for raw_kw in extract_terms(keywords.get(tier, [])):
            found_loc = "—"
            covered = False
            for loc, text_lower, text_orig in texts_lower:
                if raw_kw in text_lower:
                    snippet = text_orig[:_SNIPPET_LEN]
                    found_loc = f"{loc}: \"{snippet}{'...' if len(text_orig) > _SNIPPET_LEN else ''}\""
                    covered = True
                    break
            result[tier].append({"keyword": raw_kw, "covered": covered, "location": found_loc})

    return result


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _tier_label(tier: str) -> str:
    labels = {"P1": "P1 (Critical)", "P2": "P2 (Important)", "P3": "P3 (Nice-to-have)"}
    return labels.get(tier, tier)


def format_coverage_section(coverage: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["### Keyword Coverage", ""]
    any_content = False

    for tier in ("P1", "P2", "P3"):
        entries = coverage.get(tier, [])
        if not entries:
            continue
        any_content = True
        covered_count = sum(1 for e in entries if e["covered"])
        pct = int(covered_count / len(entries) * 100) if entries else 0
        lines.append(f"#### {_tier_label(tier)} — {covered_count}/{len(entries)} covered ({pct}%)")
        lines.append("")
        lines.append("| Keyword | Covered | Location |")
        lines.append("|---------|---------|----------|")
        for entry in entries:
            mark = "✓" if entry["covered"] else "✗"
            loc = entry["location"]
            lines.append(f"| {entry['keyword']} | {mark} | {loc} |")
        lines.append("")

    if not any_content:
        lines.append("_No keywords provided._")
        lines.append("")

    return "\n".join(lines)


def format_content_checks_section(checks: list[dict[str, str]]) -> str:
    lines = ["### Content Quality", ""]
    lines.append("| Check | Status | Detail |")
    lines.append("|-------|--------|--------|")
    for chk in checks:
        status = chk.get("status", "")
        icon = "✓" if status == "PASS" else "⚠" if status == "WARN" else "✗"
        name = chk.get("name", "")
        detail = chk.get("detail", "")
        lines.append(f"| {name} | {icon} {status} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def _format_pdf_checks_section(pdf_report: dict[str, Any]) -> str:
    lines = ["### Format Compliance", ""]
    lines.append("| Check | Status | Detail |")
    lines.append("|-------|--------|--------|")
    for chk in pdf_report.get("checks", []):
        passed = chk.get("passed", False)
        icon = "✓" if passed else "✗"
        status = "PASS" if passed else "FAIL"
        name = chk.get("name", "")
        detail_raw = chk.get("detail", {})
        detail = ", ".join(f"{k}={v}" for k, v in detail_raw.items()) if detail_raw else ""
        lines.append(f"| {name} | {icon} {status} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def _format_strategy_summary(coverage: dict[str, list[dict[str, Any]]] | None) -> str:
    lines = ["### Strategy Summary", ""]

    if coverage is None:
        lines.append("- No JD analysis available — keyword coverage skipped.")
        lines.append("")
        return "\n".join(lines)

    # Compute gaps once; reuse for both the per-tier listing and recommendation
    gaps_by_tier = {t: [e["keyword"] for e in coverage[t] if not e["covered"]] for t in ("P1", "P2", "P3")}
    grand_total = sum(len(coverage[t]) for t in ("P1", "P2", "P3"))
    grand_covered = sum(
        sum(1 for e in coverage[t] if e["covered"]) for t in ("P1", "P2", "P3")
    )
    overall_pct = int(grand_covered / grand_total * 100) if grand_total else 0

    lines.append(f"- Overall keyword coverage: {grand_covered}/{grand_total} ({overall_pct}%)")

    for tier in ("P1", "P2", "P3"):
        if gaps_by_tier[tier]:
            lines.append(f"- {_tier_label(tier)} gaps: {', '.join(gaps_by_tier[tier])}")

    if gaps_by_tier["P1"]:
        lines.append(
            f"- Recommendation: 优先在 experience 相关 bullet 中补充未覆盖的 P1 关键词：{', '.join(gaps_by_tier['P1'])}"
        )
    else:
        lines.append("- Recommendation: P1 keywords fully covered — consider reinforcing P2 gaps.")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(
    resume: dict[str, Any],
    jd_analysis: dict[str, Any] | None,
    *,
    pdf_report: dict[str, Any] | None = None,
) -> str:
    """Build and return the full quality report as a Markdown string."""
    sections = ["## Quality Check Report", ""]

    # Format compliance (PDF, optional)
    if pdf_report is not None:
        sections.append(_format_pdf_checks_section(pdf_report))

    # Content quality — pass dict directly, no temp file needed
    sections.append(format_content_checks_section(run_all_checks(resume)))

    # Keyword coverage
    if jd_analysis is not None:
        coverage = build_keyword_coverage(resume, jd_analysis)
        sections.append(format_coverage_section(coverage))
        sections.append(_format_strategy_summary(coverage))
    else:
        sections.append(_format_strategy_summary(None))

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print resume quality report to stdout (Markdown)."
    )
    parser.add_argument("--resume", required=True, help="Path to resume-working.json")
    parser.add_argument("--jd-analysis", dest="jd_analysis", help="Path to jd-analysis.json")
    parser.add_argument("--pdf", help="Path to generated PDF (optional, for format checks)")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    resume_path = Path(args.resume).expanduser().resolve()
    if not resume_path.exists():
        print(f"Error: resume file not found: {resume_path}", file=sys.stderr)
        return 1

    resume = load_json_file(resume_path)

    jd_analysis: dict[str, Any] | None = None
    if args.jd_analysis:
        jd_path = Path(args.jd_analysis).expanduser().resolve()
        if jd_path.exists():
            jd_analysis = load_json_file(jd_path)
        else:
            print(f"Warning: jd-analysis file not found: {jd_path}", file=sys.stderr)

    pdf_report: dict[str, Any] | None = None
    if args.pdf:
        pdf_path = Path(args.pdf).expanduser().resolve()
        if pdf_path.exists():
            try:
                from scripts.check_pdf_quality import check_pdf_file
                pdf_report = check_pdf_file(pdf_path)
            except Exception as exc:
                print(f"Warning: PDF check failed: {exc}", file=sys.stderr)
        else:
            print(f"Warning: PDF not found: {pdf_path}", file=sys.stderr)

    print(generate_report(resume, jd_analysis, pdf_report=pdf_report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
