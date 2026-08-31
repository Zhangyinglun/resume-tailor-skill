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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_factual_integrity import audit_resume  # noqa: E402
from scripts.check_content_quality import run_all_checks  # noqa: E402
from scripts.resume_cache_manager import validate_jd_analysis  # noqa: E402
from scripts.resume_shared import (  # noqa: E402
    extract_terms,
    load_json_file,
    normalize_skill_items,
    term_matches,
    validate_resume_content,
)

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
        category = sk.get("category", "")
        if category:
            texts.append((f"skills[{i}].category", category))
        items = sk.get("items", "")
        if isinstance(items, list):
            for j, it in enumerate(normalize_skill_items(items)):
                texts.append((f"skills[{i}].items[{j}]", it))
        elif isinstance(items, str) and items:
            texts.append((f"skills[{i}].items", items))

    for i, exp in enumerate(resume.get("experience", [])):
        title = exp.get("title", "")
        if title:
            texts.append((f"experience[{i}].title", title))
        for j, bullet in enumerate(exp.get("bullets", [])):
            texts.append((f"experience[{i}].bullets[{j}]", str(bullet)))

    for i, proj in enumerate(resume.get("projects", [])):
        name = proj.get("name", "")
        if name:
            texts.append((f"projects[{i}].name", name))
        tech = proj.get("tech", "")
        if tech:
            texts.append((f"projects[{i}].tech", tech))
        for j, bullet in enumerate(proj.get("bullets", [])):
            texts.append((f"projects[{i}].bullets[{j}]", str(bullet)))

    for i, education in enumerate(resume.get("education", [])):
        degree = education.get("degree", "")
        if degree:
            texts.append((f"education[{i}].degree", degree))

    for i, certification in enumerate(resume.get("certifications", [])):
        name = certification.get("name", "")
        if name:
            texts.append((f"certifications[{i}].name", name))

    for i, award in enumerate(resume.get("awards", [])):
        name = award.get("name", "")
        if name:
            texts.append((f"awards[{i}].name", name))

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

    result: dict[str, list[dict[str, Any]]] = {"P1": [], "P2": [], "P3": []}
    for tier in ("P1", "P2", "P3"):
        for raw_kw in extract_terms(keywords.get(tier, [])):
            locations: list[str] = []
            modules: set[str] = set()
            for loc, text_orig in texts:
                if term_matches(text_orig, raw_kw):
                    snippet = text_orig[:_SNIPPET_LEN]
                    locations.append(
                        f"{loc}: \"{snippet}{'...' if len(text_orig) > _SNIPPET_LEN else ''}\""
                    )
                    modules.add(loc.split("[", 1)[0].split(".", 1)[0])
            result[tier].append(
                {
                    "keyword": raw_kw,
                    "covered": bool(locations),
                    "location": locations[0] if locations else "—",
                    "locations": locations,
                    "module_count": len(modules),
                }
            )

    return result


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _tier_label(tier: str) -> str:
    labels = {"P1": "P1 (Critical)", "P2": "P2 (Important)", "P3": "P3 (Nice-to-have)"}
    return labels.get(tier, tier)


def _md_cell(value: Any) -> str:
    """Escape dynamic text for a Markdown table cell."""
    return str(value).replace("|", r"\|").replace("\r\n", "<br>").replace("\n", "<br>")


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
            lines.append(
                f"| {_md_cell(entry['keyword'])} | {mark} | {_md_cell(loc)} |"
            )
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
        lines.append(
            f"| {_md_cell(name)} | {icon} {status} | {_md_cell(detail)} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_factual_audit_section(factual_report: dict[str, Any]) -> str:
    lines = ["### Factual Integrity", ""]
    coverage = factual_report.get("coverage", {})
    lines.append(f"- Verdict: **{_md_cell(factual_report.get('verdict', 'UNKNOWN'))}**")
    lines.append(
        "- Manifest coverage: "
        f"{coverage.get('covered_fields', 0)}/{coverage.get('total_fields', 0)} "
        f"({coverage.get('coverage_percent', 0)}%)"
    )
    findings = factual_report.get("findings", [])
    if findings:
        lines.extend(["", "| Code | Path | Finding |", "|---|---|---|"])
        for finding in findings:
            lines.append(
                f"| {_md_cell(finding.get('code', ''))} | "
                f"{_md_cell(finding.get('path', ''))} | "
                f"{_md_cell(finding.get('message', ''))} |"
            )
    else:
        lines.append("- All substantive fields are linked to active evidence.")
    lines.append("")
    return "\n".join(lines)


def format_projection_plan_section(projection_plan: dict[str, Any]) -> str:
    lines = ["### Projection Plan", ""]
    revision = projection_plan.get("revision")
    if revision is not None:
        lines.append(f"- Plan revision: {revision}")
    status = projection_plan.get("status")
    if status is not None:
        lines.append(f"- Status: {_md_cell(status)}")

    exp_plans = projection_plan.get("experience_plans", [])
    if exp_plans:
        lines.extend([
            "",
            "#### Experience Budget",
            "| Entity | Importance | Target Bullets | Reason |",
            "|---|---|---|---|",
        ])
        for exp in exp_plans:
            entity_id = exp.get("entity_id", "")
            importance = exp.get("importance", "")
            target_bullets = exp.get("target_bullet_count", "")
            reason = exp.get("reason", "")
            lines.append(
                f"| {_md_cell(entity_id)} | {_md_cell(importance)} | "
                f"{_md_cell(target_bullets)} | {_md_cell(reason)} |"
            )

    skills_plan = projection_plan.get("skills_plan")
    if isinstance(skills_plan, dict) and skills_plan.get("groups"):
        lines.extend(["", "#### Skills Plan"])
        for group in skills_plan.get("groups", []):
            category = group.get("category", "")
            raw_items = group.get("items", [])
            item_names: list[str] = []
            for it in raw_items:
                if isinstance(it, dict):
                    item_names.append(it.get("display_term") or it.get("name", ""))
                else:
                    item_names.append(str(it))
            lines.append(f"- **{_md_cell(category)}**: {_md_cell(', '.join(item_names))}")

    opt_sections = projection_plan.get("optional_sections", [])
    if opt_sections:
        lines.extend(["", "#### Optional Section Decisions"])
        removed = [
            s for s in opt_sections
            if (s.get("decision") or s.get("action")) == "remove"
        ]
        retained = [
            s for s in opt_sections
            if (s.get("decision") or s.get("action")) != "remove"
        ]
        if removed:
            removed_desc = "; ".join(
                f"{s.get('section') or s.get('section_name')}"
                + (f" ({s.get('reason')})" if s.get("reason") else "")
                for s in removed
            )
            lines.append(f"- Removed optional sections: {removed_desc}")
        if retained:
            retained_desc = "; ".join(
                f"{s.get('section') or s.get('section_name')}"
                + (f" ({s.get('reason')})" if s.get("reason") else "")
                for s in retained
            )
            lines.append(f"- Retained optional sections: {retained_desc}")

        lines.extend([
            "",
            "| Section | Decision | Reason |",
            "|---|---|---|",
        ])
        for s in opt_sections:
            sec_name = s.get("section") or s.get("section_name", "")
            decision = s.get("decision") or s.get("action", "")
            reason = s.get("reason", "")
            lines.append(f"| {_md_cell(sec_name)} | {_md_cell(decision)} | {_md_cell(reason)} |")

    lines.append("")
    return "\n".join(lines)


def format_language_optimization_section(language_output: dict[str, Any]) -> str:
    lines = ["### Resume Language Optimization", ""]
    items = language_output.get("items", [])
    lines.append(f"- Total language items: {len(items)}")

    all_zero = True
    for item in items:
        mc = item.get("meaning_check", {})
        if (
            mc.get("facts_added")
            or mc.get("facts_removed")
            or mc.get("metrics_changed")
            or mc.get("ownership_changed") is not False
        ):
            all_zero = False
            break

    if all_zero:
        lines.append(
            "- Meaning check: Declared zero meaning changes "
            "(facts, metrics, and ownership preserved)."
        )
    else:
        lines.append(
            "- Meaning check: ⚠ Meaning changes detected in output items."
        )

    action_counts: dict[str, int] = {}
    for item in items:
        for action in item.get("style_actions", []):
            action_counts[action] = action_counts.get(action, 0) + 1

    if action_counts:
        actions_str = ", ".join(f"{k} ({v})" for k, v in sorted(action_counts.items()))
        lines.append(f"- Style actions summary: {actions_str}")
        lines.extend([
            "",
            "| Style Action | Count |",
            "|---|---|",
        ])
        for act, cnt in sorted(action_counts.items()):
            lines.append(f"| {_md_cell(act)} | {cnt} |")
    else:
        lines.append("- Style actions summary: None")

    lines.append("")
    return "\n".join(lines)


def format_content_fit_section(content_fit_feedback: dict[str, Any]) -> str:
    lines = ["### Content Fit", ""]
    verdict = content_fit_feedback.get("verdict", "UNKNOWN")
    lines.append(f"- Verdict: **{_md_cell(verdict)}**")

    revision = content_fit_feedback.get("plan_revision")
    if revision is not None:
        lines.append(f"- Plan revision: {revision}")

    page_count = content_fit_feedback.get("page_count")
    if page_count is not None:
        lines.append(f"- Page count: {page_count}")

    bottom_ws = content_fit_feedback.get("bottom_whitespace_mm")
    if bottom_ws is not None:
        lines.append(f"- Bottom whitespace: {bottom_ws} mm")
    else:
        lines.append("- Bottom whitespace: —")

    section_geo = content_fit_feedback.get("section_geometry", {})
    skills_lines = None
    if isinstance(section_geo, dict):
        skills_info = section_geo.get("skills")
        if isinstance(skills_info, dict):
            skills_lines = skills_info.get("line_count")
    if skills_lines is None:
        skills_lines = (
            content_fit_feedback.get("skills_line_count")
            or content_fit_feedback.get("skills_lines")
        )
    if skills_lines is not None:
        lines.append(f"- Skills line count: {skills_lines}")

    issues = content_fit_feedback.get("issues", [])
    if issues:
        lines.append(f"- Issues: {_md_cell(', '.join(str(i) for i in issues))}")
    else:
        lines.append("- Issues: None")

    sparse = content_fit_feedback.get("sparse_trailing_bullets", [])
    if sparse:
        lines.append(f"- Sparse trailing bullets detected: {len(sparse)}")

    lines.append("")
    return "\n".join(lines)


def format_capability_alignment_section(jd_analysis: dict[str, Any]) -> str:
    lines = ["### JD Capability Alignment", ""]
    capabilities = jd_analysis.get("capabilities", [])
    if not capabilities:
        lines.extend(["_No structured capabilities provided._", ""])
        return "\n".join(lines)
    lines.extend([
        "| Priority | Capability | Match | Evidence | Claims |",
        "|---|---|---|---|---|",
    ])
    for capability in capabilities:
        lines.append(
            f"| {_md_cell(capability.get('priority', ''))} | "
            f"{_md_cell(capability.get('name', ''))} | "
            f"{_md_cell(capability.get('match_type', ''))} | "
            f"{_md_cell(capability.get('evidence_state', ''))} | "
            f"{_md_cell(', '.join(str(item) for item in capability.get('claim_ids', [])) or '—')} |"
        )
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
        lines.append(
            f"| {_md_cell(name)} | {icon} {status} | {_md_cell(detail)} |"
        )
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
            "- Recommendation: Verify whether existing evidence supports each P1 gap. "
            f"Add only supported terms; otherwise retain the gap: {', '.join(gaps_by_tier['P1'])}"
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
    factual_report: dict[str, Any] | None = None,
    projection_plan: dict[str, Any] | None = None,
    language_output: dict[str, Any] | None = None,
    content_fit_feedback: dict[str, Any] | None = None,
) -> str:
    """Build and return the full quality report as a Markdown string."""
    sections = ["## Quality Check Report", ""]

    if factual_report is not None:
        sections.append(format_factual_audit_section(factual_report))

    if projection_plan is not None:
        sections.append(format_projection_plan_section(projection_plan))

    if language_output is not None:
        sections.append(format_language_optimization_section(language_output))

    if content_fit_feedback is not None:
        sections.append(format_content_fit_section(content_fit_feedback))

    # Format compliance (PDF, optional)
    if pdf_report is not None:
        sections.append(_format_pdf_checks_section(pdf_report))

    # Content quality — pass dict directly, no temp file needed
    sections.append(format_content_checks_section(run_all_checks(resume)))

    # Keyword coverage
    if jd_analysis is not None:
        sections.append(format_capability_alignment_section(jd_analysis))
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
    parser.add_argument("--manifest", help="Path to resume-changes.json")
    parser.add_argument("--evidence", help="Path to candidate-evidence.json")
    parser.add_argument("--base", help="Path to base-resume.json")
    parser.add_argument(
        "--projection-plan",
        dest="projection_plan",
        help="Path to projection-plan.json (optional)",
    )
    parser.add_argument(
        "--language-output",
        dest="language_output",
        help="Path to language-output.json (optional)",
    )
    parser.add_argument(
        "--content-fit-feedback",
        dest="content_fit_feedback",
        help="Path to content-fit-feedback.json (optional)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    resume_path = Path(args.resume).expanduser().resolve()
    if not resume_path.exists():
        print(f"Error: resume file not found: {resume_path}", file=sys.stderr)
        return 1

    try:
        resume = load_json_file(resume_path)
        validate_resume_content(resume, require_non_empty=True)
    except (OSError, ValueError) as exc:
        print(f"Error: invalid resume content: {exc}", file=sys.stderr)
        return 1

    jd_analysis: dict[str, Any] | None = None
    incomplete_inputs = False
    if args.jd_analysis:
        jd_path = Path(args.jd_analysis).expanduser().resolve()
        if jd_path.exists():
            try:
                jd_analysis = load_json_file(jd_path)
                validate_jd_analysis(jd_analysis)
            except (OSError, ValueError) as exc:
                print(f"Error: invalid JD analysis: {exc}", file=sys.stderr)
                return 1
        else:
            print(f"Warning: jd-analysis file not found: {jd_path}", file=sys.stderr)
            incomplete_inputs = True

    factual_report: dict[str, Any] | None = None
    factual_paths = (args.manifest, args.evidence, args.base)
    if any(factual_paths):
        if not all(factual_paths):
            print(
                "Error: --manifest, --evidence, and --base must be provided together.",
                file=sys.stderr,
            )
            return 1
        try:
            factual_report = audit_resume(
                resume,
                load_json_file(Path(args.manifest).expanduser().resolve()),
                load_json_file(Path(args.evidence).expanduser().resolve()),
                base_resume=load_json_file(Path(args.base).expanduser().resolve()),
            )
        except (OSError, ValueError) as exc:
            print(f"Error: factual audit failed: {exc}", file=sys.stderr)
            return 1

    projection_plan: dict[str, Any] | None = None
    if args.projection_plan:
        plan_path = Path(args.projection_plan).expanduser().resolve()
        if plan_path.exists():
            try:
                projection_plan = load_json_file(plan_path)
            except (OSError, ValueError) as exc:
                print(f"Error: invalid projection plan: {exc}", file=sys.stderr)
                return 1
        else:
            print(f"Warning: projection-plan file not found: {plan_path}", file=sys.stderr)
            incomplete_inputs = True

    language_output: dict[str, Any] | None = None
    if args.language_output:
        lang_path = Path(args.language_output).expanduser().resolve()
        if lang_path.exists():
            try:
                language_output = load_json_file(lang_path)
            except (OSError, ValueError) as exc:
                print(f"Error: invalid language output: {exc}", file=sys.stderr)
                return 1
        else:
            print(f"Warning: language-output file not found: {lang_path}", file=sys.stderr)
            incomplete_inputs = True

    content_fit_feedback: dict[str, Any] | None = None
    if args.content_fit_feedback:
        fit_path = Path(args.content_fit_feedback).expanduser().resolve()
        if fit_path.exists():
            try:
                content_fit_feedback = load_json_file(fit_path)
            except (OSError, ValueError) as exc:
                print(f"Error: invalid content fit feedback: {exc}", file=sys.stderr)
                return 1
        else:
            print(f"Warning: content-fit-feedback file not found: {fit_path}", file=sys.stderr)
            incomplete_inputs = True

    pdf_report: dict[str, Any] | None = None
    if args.pdf:
        pdf_path = Path(args.pdf).expanduser().resolve()
        if pdf_path.exists():
            try:
                from scripts.check_pdf_quality import check_pdf_file
                pdf_report = check_pdf_file(pdf_path)
            except Exception as exc:
                print(f"Warning: PDF check failed: {exc}", file=sys.stderr)
                incomplete_inputs = True
        else:
            print(f"Warning: PDF not found: {pdf_path}", file=sys.stderr)
            incomplete_inputs = True

    content_checks = run_all_checks(resume)
    print(
        generate_report(
            resume,
            jd_analysis,
            pdf_report=pdf_report,
            factual_report=factual_report,
            projection_plan=projection_plan,
            language_output=language_output,
            content_fit_feedback=content_fit_feedback,
        )
    )
    content_ok = all(item.get("status") == "PASS" for item in content_checks)
    pdf_ok = pdf_report is None or pdf_report.get("verdict") == "PASS"
    factual_ok = factual_report is None or factual_report.get("verdict") == "PASS"
    if incomplete_inputs:
        return 1
    return 0 if content_ok and pdf_ok and factual_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
