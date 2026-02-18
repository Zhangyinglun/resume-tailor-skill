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
        "--min-bottom-mm",
        type=float,
        default=3.0,
        help="Minimum bottom margin (mm, default 3)",
    )
    parser.add_argument(
        "--max-bottom-mm",
        type=float,
        default=8.0,
        help="Maximum bottom margin (mm, default 8)",
    )
    parser.add_argument(
        "--min-top-mm",
        type=float,
        default=3.0,
        help="Minimum top margin (mm, default 3)",
    )
    parser.add_argument(
        "--max-top-mm",
        type=float,
        default=20.0,
        help="Maximum top margin (mm, default 20)",
    )
    parser.add_argument(
        "--min-side-mm",
        type=float,
        default=10.0,
        help="Minimum left/right margin (mm, default 10)",
    )
    parser.add_argument(
        "--max-side-mm",
        type=float,
        default=25.0,
        help="Maximum left/right margin (mm, default 25)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON (machine-readable)",
    )
    return parser.parse_args()


def estimate_page_margins_mm(page: Any) -> dict[str, float] | None:
    words = page.extract_words() or []
    if not words:
        return None

    tops = [float(word["top"]) for word in words if "top" in word]
    bottoms = [float(word["bottom"]) for word in words if "bottom" in word]
    lefts = [float(word["x0"]) for word in words if "x0" in word]
    rights = [float(word["x1"]) for word in words if "x1" in word]

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


def estimate_bottom_margin_mm(page: Any) -> float | None:
    margins = estimate_page_margins_mm(page)
    if margins is None:
        return None
    return margins["bottom"]


def check_sections(text: str) -> list[str]:
    upper_text = text.upper()
    missing = []
    for section_name, options in SECTION_KEYWORDS.items():
        if not any(option in upper_text for option in options):
            missing.append(section_name)
    return missing


def check_contact_presence(text: str) -> tuple[bool, bool, bool]:
    has_email = bool(EMAIL_PATTERN.search(text))
    has_phone = bool(PHONE_PATTERN.search(text))
    has_linkedin = bool(LINKEDIN_PATTERN.search(text))
    return has_email, has_phone, has_linkedin


def check_keyword_coverage(text: str, keywords: list[str]) -> list[str]:
    if not keywords:
        return []

    lower_text = text.lower()
    missing = [keyword for keyword in keywords if keyword.lower() not in lower_text]
    return missing


def check_layout_warnings(lines: list[str]) -> list[str]:
    issues: list[str] = []

    role_time_pattern = re.compile(
        r"^[A-Za-z][A-Za-z/&,\-\s]{2,70}\s+\d{4}\s*-\s*(?:\d{4}|Present)$"
    )
    company_hint_pattern = re.compile(
        r"(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Company|University|College|Institute)",
        re.IGNORECASE,
    )

    for index, line in enumerate(lines[:-1]):
        if role_time_pattern.match(line):
            next_line = lines[index + 1]
            if company_hint_pattern.search(next_line) and "|" not in line:
                issues.append(
                    f"Suspected inverted experience entry: {line} -> {next_line}"
                )

    for index in range(len(lines) - 1):
        if lines[index] == lines[index + 1]:
            issues.append(f"Found consecutive duplicate line: {lines[index]}")

    return issues


def print_result(label: str, passed: bool, ok_message: str, fail_message: str) -> None:
    if passed:
        print(f"{label}: ✓ {ok_message}")
    else:
        print(f"{label}: ✗ {fail_message}")


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

    one_page = page_count == 1
    checks.append(
        {
            "name": "page_count",
            "passed": one_page,
            "detail": {"count": page_count, "expected": 1},
        }
    )

    is_a4 = (
        abs(width_mm - A4_WIDTH_MM) <= A4_TOLERANCE_MM
        and abs(height_mm - A4_HEIGHT_MM) <= A4_TOLERANCE_MM
    )
    checks.append(
        {
            "name": "page_size",
            "passed": is_a4,
            "detail": {
                "width_mm": round(width_mm, 1),
                "height_mm": round(height_mm, 1),
            },
        }
    )

    checks.append({"name": "text_layer", "passed": has_text, "detail": {}})

    checks.append(
        {
            "name": "html_leak",
            "passed": html_leak_count == 0,
            "detail": {"leak_count": html_leak_count},
        }
    )

    unique_placeholders = sorted(set(placeholders))
    placeholders_ok = len(placeholders) == 0
    checks.append(
        {
            "name": "placeholder_content",
            "passed": placeholders_ok,
            "detail": {"count": len(placeholders), "found": unique_placeholders},
        }
    )

    bottom_ok = True
    top_ok = True
    left_ok = True
    right_ok = True
    margin_detail: dict[str, Any] = {"available": margins is not None}

    if margins is not None:
        bottom_ok = margin_within_range(
            margins["bottom"],
            margin_thresholds["min_bottom_mm"],
            margin_thresholds["max_bottom_mm"],
        )
        top_ok = margin_within_range(
            margins["top"],
            margin_thresholds["min_top_mm"],
            margin_thresholds["max_top_mm"],
        )
        left_ok = margin_within_range(
            margins["left"],
            margin_thresholds["min_side_mm"],
            margin_thresholds["max_side_mm"],
        )
        right_ok = margin_within_range(
            margins["right"],
            margin_thresholds["min_side_mm"],
            margin_thresholds["max_side_mm"],
        )
        margin_detail.update(
            {
                "top_mm": round(margins["top"], 2),
                "bottom_mm": round(margins["bottom"], 2),
                "left_mm": round(margins["left"], 2),
                "right_mm": round(margins["right"], 2),
            }
        )

    checks.append(
        {"name": "bottom_margin", "passed": bottom_ok, "detail": margin_detail}
    )
    checks.append({"name": "top_margin", "passed": top_ok, "detail": margin_detail})
    checks.append(
        {
            "name": "side_margins",
            "passed": left_ok and right_ok,
            "detail": margin_detail,
        }
    )

    sections_ok = not missing_sections
    checks.append(
        {
            "name": "section_completeness",
            "passed": sections_ok,
            "detail": {"missing": missing_sections},
        }
    )

    has_email = contact.get("email", False)
    has_phone = contact.get("phone", False)
    has_linkedin = contact.get("linkedin", False)
    contact_ok = has_email and (has_phone or has_linkedin)
    checks.append(
        {
            "name": "contact_info",
            "passed": contact_ok,
            "detail": {
                "email": has_email,
                "phone": has_phone,
                "linkedin": has_linkedin,
            },
        }
    )

    keyword_ok = (not provided_keywords) or (not missing_keywords)
    checks.append(
        {
            "name": "keyword_coverage",
            "passed": keyword_ok,
            "detail": {"provided": len(provided_keywords), "missing": missing_keywords},
        }
    )

    checks.append(
        {
            "name": "layout_warnings",
            "passed": True,
            "detail": {"warnings": layout_warnings},
        }
    )

    critical_pass = all(check["passed"] for check in checks[:11])

    return {
        "verdict": "PASS" if critical_pass else "NEED-ADJUSTMENT",
        "checks": checks,
    }


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()

    if not pdf_path.exists():
        print(f"Error: File does not exist: {pdf_path}", file=sys.stderr)
        return 1

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        first_page = pdf.pages[0]

        width_mm = points_to_mm(first_page.width)
        height_mm = points_to_mm(first_page.height)

        text_pages = [(page.extract_text() or "") for page in pdf.pages]
        full_text = "\n".join(text_pages)
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        margins = estimate_page_margins_mm(first_page)
        missing_sections = check_sections(full_text)
        has_email, has_phone, has_linkedin = check_contact_presence(full_text)
        missing_keywords = check_keyword_coverage(full_text, args.keyword)
        layout_warnings = check_layout_warnings(lines)

        html_leaks = HTML_TAG_PATTERN.findall(full_text)

    placeholders = PLACEHOLDER_PATTERN.findall(full_text)
    unique_placeholders = sorted(set(placeholders))

    one_page = page_count == 1
    is_a4 = (
        abs(width_mm - A4_WIDTH_MM) <= A4_TOLERANCE_MM
        and abs(height_mm - A4_HEIGHT_MM) <= A4_TOLERANCE_MM
    )
    has_text = bool(full_text.strip())
    no_html = not html_leaks
    sections_ok = not missing_sections

    bottom_margin_ok = True
    top_margin_ok = True
    left_margin_ok = True
    right_margin_ok = True
    bottom_margin_mm: float | None = None
    top_margin_mm: float | None = None
    left_margin_mm: float | None = None
    right_margin_mm: float | None = None
    if margins is not None:
        bottom_margin_mm = margins["bottom"]
        top_margin_mm = margins["top"]
        left_margin_mm = margins["left"]
        right_margin_mm = margins["right"]
        bottom_margin_ok = margin_within_range(
            bottom_margin_mm, args.min_bottom_mm, args.max_bottom_mm
        )
        top_margin_ok = margin_within_range(
            top_margin_mm, args.min_top_mm, args.max_top_mm
        )
        left_margin_ok = margin_within_range(
            left_margin_mm, args.min_side_mm, args.max_side_mm
        )
        right_margin_ok = margin_within_range(
            right_margin_mm, args.min_side_mm, args.max_side_mm
        )

    contact_ok = has_email and (has_phone or has_linkedin)

    if args.json_output:
        report = build_quality_report(
            page_count=page_count,
            width_mm=width_mm,
            height_mm=height_mm,
            has_text=has_text,
            html_leak_count=len(html_leaks),
            placeholders=placeholders,
            margins=margins,
            missing_sections=missing_sections,
            contact={"email": has_email, "phone": has_phone, "linkedin": has_linkedin},
            missing_keywords=missing_keywords,
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
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["verdict"] == "PASS" else 2

    print("=" * 80)
    print(f"PDF Quality Check: {pdf_path.name}")
    print("=" * 80)

    print_result(
        "1. Page Count",
        one_page,
        "1 page",
        f"Current {page_count} pages (should be 1 page)",
    )
    print_result(
        "2. Page Size",
        is_a4,
        f"A4 ({width_mm:.1f}mm x {height_mm:.1f}mm)",
        f"Not A4 ({width_mm:.1f}mm x {height_mm:.1f}mm)",
    )
    print_result(
        "3. Text Layer", has_text, "Extractable text", "No body text extracted"
    )
    print_result(
        "4. HTML Tag Leakage",
        no_html,
        "No leakage found",
        f"Found {len(html_leaks)} suspected HTML tags",
    )

    if placeholders:
        print(
            f"5. Placeholder Content: ✗ Found {len(placeholders)} placeholder(s): {', '.join(unique_placeholders)}"
        )
    else:
        print("5. Placeholder Content: ✓ No placeholder content found")

    if margins is None:
        print(
            "6. Bottom Margin: ! Unable to auto-estimate (manual verification recommended)"
        )
        print(
            "7. Top Margin: ! Unable to auto-estimate (manual verification recommended)"
        )
        print(
            "8. Left/Right Margins: ! Unable to auto-estimate (manual verification recommended)"
        )
    else:
        print_result(
            "6. Bottom Margin",
            bottom_margin_ok,
            f"{bottom_margin_mm:.2f}mm (target {args.min_bottom_mm}-{args.max_bottom_mm}mm)",
            f"{bottom_margin_mm:.2f}mm (exceeds target {args.min_bottom_mm}-{args.max_bottom_mm}mm)",
        )
        print_result(
            "7. Top Margin",
            top_margin_ok,
            f"{top_margin_mm:.2f}mm (target {args.min_top_mm}-{args.max_top_mm}mm)",
            f"{top_margin_mm:.2f}mm (exceeds target {args.min_top_mm}-{args.max_top_mm}mm)",
        )
        side_margin_ok = left_margin_ok and right_margin_ok
        if side_margin_ok:
            print(
                f"8. Left/Right Margins: ✓ left {left_margin_mm:.2f}mm, right {right_margin_mm:.2f}mm "
                f"(target {args.min_side_mm}-{args.max_side_mm}mm)"
            )
        else:
            print(
                f"8. Left/Right Margins: ✗ left {left_margin_mm:.2f}mm, right {right_margin_mm:.2f}mm "
                f"(target {args.min_side_mm}-{args.max_side_mm}mm)"
            )

    if sections_ok:
        print(
            "9. Section Completeness: ✓ Summary/Skills/Experience/Education all identified"
        )
    else:
        print(
            f"9. Section Completeness: ✗ Missing sections: {', '.join(missing_sections)}"
        )

    print_result(
        "10. Contact Info",
        contact_ok,
        "Detected Email + (Phone or LinkedIn)",
        "Incomplete contact info (need at least Email + Phone/LinkedIn)",
    )

    if args.keyword:
        if not missing_keywords:
            print(f"11. Keyword Coverage: ✓ All {len(args.keyword)} keywords matched")
        else:
            print(
                f"11. Keyword Coverage: ✗ Missing keywords: {', '.join(missing_keywords)}"
            )
    else:
        print("11. Keyword Coverage: ! No keywords provided, skipped")

    if layout_warnings:
        print("12. Layout Warnings: ! Potential issues found")
        for issue in layout_warnings:
            print(f"   - {issue}")
    else:
        print("12. Layout Warnings: ✓ No obvious issues found")

    critical_pass = all(
        [
            one_page,
            is_a4,
            has_text,
            no_html,
            not placeholders,
            sections_ok,
            contact_ok,
            bottom_margin_ok,
            top_margin_ok,
            left_margin_ok,
            right_margin_ok,
            (not args.keyword) or (not missing_keywords),
        ]
    )

    print("=" * 80)
    if critical_pass:
        print("Final Verdict: PASS")
        print("=" * 80)
        return 0

    print("Final Verdict: NEED-ADJUSTMENT")
    print("=" * 80)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
