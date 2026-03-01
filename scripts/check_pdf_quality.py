#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resume PDF quality check script (general version)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pdfplumber

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
A4_TOLERANCE_MM = 1.0

SECTION_KEYWORDS = {
    "Summary": ("SUMMARY", "PROFESSIONAL SUMMARY"),
    "Skills": ("SKILLS", "TECHNICAL SKILLS"),
    "Experience": ("EXPERIENCE", "PROFESSIONAL EXPERIENCE", "WORK EXPERIENCE"),
    "Education": ("EDUCATION",),
}

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d()\-\s]{7,}\d)")
LINKEDIN_PATTERN = re.compile(r"linkedin\.com/", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"</?[A-Za-z][^>]*>")
PLACEHOLDER_PATTERN = re.compile(
    r"\[(?:To be filled|Dates|Degree|School|Certification|Award|Project|Company|Title|Location)\]",
    re.IGNORECASE,
)


def points_to_mm(value: float) -> float:
    return value * 25.4 / 72.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check if resume PDF meets format and text readability requirements."
    )
    parser.add_argument("pdf_path", help="PDF file path to check")
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Core keywords (can be repeated, use multiple --keyword flags)",
    )
    parser.add_argument(
        "--min-bottom-mm", type=float, default=3.0,
        help="Minimum bottom margin (mm, default 3)",
    )
    parser.add_argument(
        "--max-bottom-mm", type=float, default=12.0,
        help="Maximum bottom margin (mm, default 12)",
    )
    parser.add_argument(
        "--min-top-mm", type=float, default=3.0,
        help="Minimum top margin (mm, default 3)",
    )
    parser.add_argument(
        "--max-top-mm", type=float, default=20.0,
        help="Maximum top margin (mm, default 20)",
    )
    parser.add_argument(
        "--min-side-mm", type=float, default=10.0,
        help="Minimum left/right margin (mm, default 10)",
    )
    parser.add_argument(
        "--max-side-mm", type=float, default=25.0,
        help="Maximum left/right margin (mm, default 25)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output results as JSON (machine-readable)",
    )
    return parser.parse_args()


def estimate_page_margins_mm(page: Any) -> dict[str, float] | None:
    words = page.extract_words() or []
    if not words:
        return None

    tops = [float(w["top"]) for w in words if "top" in w]
    bottoms = [float(w["bottom"]) for w in words if "bottom" in w]
    lefts = [float(w["x0"]) for w in words if "x0" in w]
    rights = [float(w["x1"]) for w in words if "x1" in w]

    if not tops or not bottoms or not lefts or not rights:
        return None

    return {
        "top": points_to_mm(min(tops)),
        "bottom": points_to_mm(page.height - max(bottoms)),
        "left": points_to_mm(min(lefts)),
        "right": points_to_mm(page.width - max(rights)),
    }


def margin_within_range(value: float, minimum: float, maximum: float) -> bool:
    return minimum <= value <= maximum


def build_quality_report(
    *,
    page_count: int,
    width_mm: float,
    height_mm: float,
    has_text: bool,
    html_leak_count: int,
    placeholders: list[str],
    margins: dict[str, float] | None,
    missing_sections: list[str],
    contact: dict[str, bool],
    missing_keywords: list[str],
    provided_keywords: list[str],
    layout_warnings: list[str],
    margin_thresholds: dict[str, float],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    checks.append({
        "name": "page_count",
        "passed": page_count == 1,
        "detail": {"count": page_count, "expected": 1},
    })

    checks.append({
        "name": "page_size",
        "passed": (
            abs(width_mm - A4_WIDTH_MM) <= A4_TOLERANCE_MM
            and abs(height_mm - A4_HEIGHT_MM) <= A4_TOLERANCE_MM
        ),
        "detail": {"width_mm": round(width_mm, 1), "height_mm": round(height_mm, 1)},
    })

    checks.append({"name": "text_layer", "passed": has_text, "detail": {}})
    checks.append({
        "name": "html_leak",
        "passed": html_leak_count == 0,
        "detail": {"leak_count": html_leak_count},
    })
    checks.append({
        "name": "placeholder_content",
        "passed": len(placeholders) == 0,
        "detail": {"count": len(placeholders), "found": sorted(set(placeholders))},
    })

    # Margin checks
    margin_detail: dict[str, Any] = {"available": margins is not None}
    margin_ok = {"bottom": True, "top": True, "left": True, "right": True}

    if margins is not None:
        margin_ok["bottom"] = margin_within_range(
            margins["bottom"], margin_thresholds["min_bottom_mm"], margin_thresholds["max_bottom_mm"])
        margin_ok["top"] = margin_within_range(
            margins["top"], margin_thresholds["min_top_mm"], margin_thresholds["max_top_mm"])
        margin_ok["left"] = margin_within_range(
            margins["left"], margin_thresholds["min_side_mm"], margin_thresholds["max_side_mm"])
        margin_ok["right"] = margin_within_range(
            margins["right"], margin_thresholds["min_side_mm"], margin_thresholds["max_side_mm"])
        margin_detail.update({
            f"{side}_mm": round(margins[side], 2) for side in ("top", "bottom", "left", "right")
        })

    checks.append({"name": "bottom_margin", "passed": margin_ok["bottom"], "detail": margin_detail})
    checks.append({"name": "top_margin", "passed": margin_ok["top"], "detail": margin_detail})
    checks.append({"name": "side_margins", "passed": margin_ok["left"] and margin_ok["right"], "detail": margin_detail})

    checks.append({
        "name": "section_completeness",
        "passed": not missing_sections,
        "detail": {"missing": missing_sections},
    })

    contact_ok = contact.get("email", False) and (contact.get("phone", False) or contact.get("linkedin", False))
    checks.append({
        "name": "contact_info",
        "passed": contact_ok,
        "detail": contact,
    })

    checks.append({
        "name": "keyword_coverage",
        "passed": (not provided_keywords) or (not missing_keywords),
        "detail": {"provided": len(provided_keywords), "missing": missing_keywords},
    })

    checks.append({
        "name": "layout_warnings",
        "passed": True,
        "detail": {"warnings": layout_warnings},
    })

    critical_pass = all(check["passed"] for check in checks[:11])
    return {"verdict": "PASS" if critical_pass else "NEED-ADJUSTMENT", "checks": checks}


def _format_text_report(report: dict[str, Any], pdf_name: str, args: argparse.Namespace) -> str:
    """Format quality report as human-readable text."""
    lines = ["=" * 80, f"PDF Quality Check: {pdf_name}", "=" * 80]
    checks = {c["name"]: c for c in report["checks"]}

    # Simple pass/fail checks
    _simple = [
        ("1. Page Count", "page_count",
         lambda d: "1 page", lambda d: f"Current {d['count']} pages (should be 1 page)"),
        ("2. Page Size", "page_size",
         lambda d: f"A4 ({d['width_mm']}mm x {d['height_mm']}mm)",
         lambda d: f"Not A4 ({d['width_mm']}mm x {d['height_mm']}mm)"),
        ("3. Text Layer", "text_layer",
         lambda _: "Extractable text", lambda _: "No body text extracted"),
        ("4. HTML Tag Leakage", "html_leak",
         lambda _: "No leakage found",
         lambda d: f"Found {d['leak_count']} suspected HTML tags"),
    ]
    for label, name, ok_msg, fail_msg in _simple:
        c = checks[name]
        mark = "\u2713" if c["passed"] else "\u2717"
        msg = ok_msg(c["detail"]) if c["passed"] else fail_msg(c["detail"])
        lines.append(f"{label}: {mark} {msg}")

    # Placeholder
    ph = checks["placeholder_content"]
    if ph["passed"]:
        lines.append("5. Placeholder Content: \u2713 No placeholder content found")
    else:
        found = ", ".join(ph["detail"]["found"])
        lines.append(f"5. Placeholder Content: \u2717 Found {ph['detail']['count']} placeholder(s): {found}")

    # Margins
    margin_detail = checks["bottom_margin"]["detail"]
    if not margin_detail.get("available"):
        for i, label in [(6, "Bottom Margin"), (7, "Top Margin"), (8, "Left/Right Margins")]:
            lines.append(f"{i}. {label}: ! Unable to auto-estimate (manual verification recommended)")
    else:
        for i, name, side, lo, hi in [
            (6, "bottom_margin", "bottom", args.min_bottom_mm, args.max_bottom_mm),
            (7, "top_margin", "top", args.min_top_mm, args.max_top_mm),
        ]:
            c = checks[name]
            val = margin_detail[f"{side}_mm"]
            mark = "\u2713" if c["passed"] else "\u2717"
            status = "target" if c["passed"] else "exceeds target"
            lines.append(f"{i}. {name.replace('_', ' ').title()}: {mark} {val:.2f}mm ({status} {lo}-{hi}mm)")

        side_ok = checks["side_margins"]["passed"]
        l_mm, r_mm = margin_detail["left_mm"], margin_detail["right_mm"]
        mark = "\u2713" if side_ok else "\u2717"
        lines.append(
            f"8. Left/Right Margins: {mark} left {l_mm:.2f}mm, right {r_mm:.2f}mm "
            f"(target {args.min_side_mm}-{args.max_side_mm}mm)"
        )

    # Sections
    sc = checks["section_completeness"]
    if sc["passed"]:
        lines.append("9. Section Completeness: \u2713 Summary/Skills/Experience/Education all identified")
    else:
        lines.append(f"9. Section Completeness: \u2717 Missing sections: {', '.join(sc['detail']['missing'])}")

    # Contact
    cc = checks["contact_info"]
    mark = "\u2713" if cc["passed"] else "\u2717"
    msg = "Detected Email + (Phone or LinkedIn)" if cc["passed"] else "Incomplete contact info (need at least Email + Phone/LinkedIn)"
    lines.append(f"10. Contact Info: {mark} {msg}")

    # Keywords
    kw = checks["keyword_coverage"]
    if not args.keyword:
        lines.append("11. Keyword Coverage: ! No keywords provided, skipped")
    elif kw["passed"]:
        lines.append(f"11. Keyword Coverage: \u2713 All {len(args.keyword)} keywords matched")
    else:
        lines.append(f"11. Keyword Coverage: \u2717 Missing keywords: {', '.join(kw['detail']['missing'])}")

    # Layout warnings
    lw = checks["layout_warnings"]
    if lw["detail"]["warnings"]:
        lines.append("12. Layout Warnings: ! Potential issues found")
        for issue in lw["detail"]["warnings"]:
            lines.append(f"   - {issue}")
    else:
        lines.append("12. Layout Warnings: \u2713 No obvious issues found")

    lines.append("=" * 80)
    lines.append(f"Final Verdict: {report['verdict']}")
    lines.append("=" * 80)
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()

    if not pdf_path.exists():
        print(f"Error: File does not exist: {pdf_path}", file=sys.stderr)
        return 1

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        full_text = "\n".join((page.extract_text() or "") for page in pdf.pages)
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        # Collect all data
        upper_text = full_text.upper()
        missing_sections = [
            name for name, options in SECTION_KEYWORDS.items()
            if not any(opt in upper_text for opt in options)
        ]

        # Layout warnings
        layout_warnings: list[str] = []
        role_time = re.compile(r"^[A-Za-z][A-Za-z/&,\-\s]{2,70}\s+\d{4}\s*-\s*(?:\d{4}|Present)$")
        company_hint = re.compile(r"(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Company|University|College|Institute)", re.IGNORECASE)
        for i, line in enumerate(lines[:-1]):
            if role_time.match(line) and company_hint.search(lines[i + 1]) and "|" not in line:
                layout_warnings.append(f"Suspected inverted experience entry: {line} -> {lines[i + 1]}")
            if line == lines[i + 1]:
                layout_warnings.append(f"Found consecutive duplicate line: {line}")

        report = build_quality_report(
            page_count=len(pdf.pages),
            width_mm=points_to_mm(first_page.width),
            height_mm=points_to_mm(first_page.height),
            has_text=bool(full_text.strip()),
            html_leak_count=len(HTML_TAG_PATTERN.findall(full_text)),
            placeholders=PLACEHOLDER_PATTERN.findall(full_text),
            margins=estimate_page_margins_mm(first_page),
            missing_sections=missing_sections,
            contact={
                "email": bool(EMAIL_PATTERN.search(full_text)),
                "phone": bool(PHONE_PATTERN.search(full_text)),
                "linkedin": bool(LINKEDIN_PATTERN.search(full_text)),
            },
            missing_keywords=[kw for kw in args.keyword if kw.lower() not in full_text.lower()] if args.keyword else [],
            provided_keywords=args.keyword,
            layout_warnings=layout_warnings,
            margin_thresholds={
                "min_bottom_mm": args.min_bottom_mm,
                "max_bottom_mm": args.max_bottom_mm,
                "min_top_mm": args.min_top_mm,
                "max_top_mm": args.max_top_mm,
                "min_side_mm": args.min_side_mm,
                "max_side_mm": args.max_side_mm,
            },
        )

    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_format_text_report(report, pdf_path.name, args))

    return 0 if report["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
