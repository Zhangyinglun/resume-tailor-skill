#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简历 PDF 质量检查脚本（通用版）。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

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


def points_to_mm(value: float) -> float:
    return value * 25.4 / 72.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检测简历 PDF 是否满足格式与文本可读性要求。")
    parser.add_argument("pdf_path", help="待检测 PDF 文件路径")
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="核心关键词（可重复传入，多次 --keyword）",
    )
    parser.add_argument(
        "--min-bottom-mm",
        type=float,
        default=3.0,
        help="底部留白最小值（mm，默认 3）",
    )
    parser.add_argument(
        "--max-bottom-mm",
        type=float,
        default=8.0,
        help="底部留白最大值（mm，默认 8）",
    )
    return parser.parse_args()


def estimate_bottom_margin_mm(page: pdfplumber.page.Page) -> float | None:
    words = page.extract_words() or []
    bottoms = [float(word["bottom"]) for word in words if "bottom" in word]
    if not bottoms:
        return None

    max_bottom = max(bottoms)
    margin_points = page.height - max_bottom
    return points_to_mm(margin_points)


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
                issues.append(f"疑似经历条目倒置: {line} -> {next_line}")

    for index in range(len(lines) - 1):
        if lines[index] == lines[index + 1]:
            issues.append(f"发现连续重复行: {lines[index]}")

    return issues


def print_result(label: str, passed: bool, ok_message: str, fail_message: str) -> None:
    if passed:
        print(f"{label}: ✓ {ok_message}")
    else:
        print(f"{label}: ✗ {fail_message}")


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()

    if not pdf_path.exists():
        print(f"错误: 文件不存在: {pdf_path}", file=sys.stderr)
        return 1

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        first_page = pdf.pages[0]

        width_mm = points_to_mm(first_page.width)
        height_mm = points_to_mm(first_page.height)

        text_pages = [(page.extract_text() or "") for page in pdf.pages]
        full_text = "\n".join(text_pages)
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        bottom_margin_mm = estimate_bottom_margin_mm(first_page)
        missing_sections = check_sections(full_text)
        has_email, has_phone, has_linkedin = check_contact_presence(full_text)
        missing_keywords = check_keyword_coverage(full_text, args.keyword)
        layout_warnings = check_layout_warnings(lines)

        html_leaks = HTML_TAG_PATTERN.findall(full_text)

    print("=" * 80)
    print(f"PDF 质量检测: {pdf_path.name}")
    print("=" * 80)

    one_page = page_count == 1
    is_a4 = (
        abs(width_mm - A4_WIDTH_MM) <= A4_TOLERANCE_MM
        and abs(height_mm - A4_HEIGHT_MM) <= A4_TOLERANCE_MM
    )
    has_text = bool(full_text.strip())
    no_html = not html_leaks
    sections_ok = not missing_sections

    bottom_margin_ok = True
    if bottom_margin_mm is not None:
        bottom_margin_ok = args.min_bottom_mm <= bottom_margin_mm <= args.max_bottom_mm

    contact_ok = has_email and (has_phone or has_linkedin)

    print_result("1. 页数", one_page, "1 页", f"当前 {page_count} 页（应为 1 页）")
    print_result(
        "2. 页面尺寸",
        is_a4,
        f"A4 ({width_mm:.1f}mm x {height_mm:.1f}mm)",
        f"非 A4 ({width_mm:.1f}mm x {height_mm:.1f}mm)",
    )
    print_result("3. 文本层", has_text, "可提取文本", "未提取到正文文本")
    print_result("4. HTML 标签泄漏", no_html, "未发现泄漏", f"发现 {len(html_leaks)} 处疑似 HTML 标签")

    if bottom_margin_mm is None:
        print("5. 底部留白: ! 无法自动估算（建议目视确认）")
    else:
        print_result(
            "5. 底部留白",
            bottom_margin_ok,
            f"{bottom_margin_mm:.2f}mm（目标 {args.min_bottom_mm}-{args.max_bottom_mm}mm）",
            f"{bottom_margin_mm:.2f}mm（超出目标 {args.min_bottom_mm}-{args.max_bottom_mm}mm）",
        )

    if sections_ok:
        print("6. 模块完整性: ✓ Summary/Skills/Experience/Education 均可识别")
    else:
        print(f"6. 模块完整性: ✗ 缺失模块: {', '.join(missing_sections)}")

    print_result(
        "7. 联系信息",
        contact_ok,
        "检测到 Email + (Phone 或 LinkedIn)",
        "联系信息不完整（至少需要 Email + Phone/LinkedIn 其一）",
    )

    if args.keyword:
        if not missing_keywords:
            print(f"8. 关键词覆盖: ✓ {len(args.keyword)} 个关键词全部命中")
        else:
            print(f"8. 关键词覆盖: ✗ 缺失关键词: {', '.join(missing_keywords)}")
    else:
        print("8. 关键词覆盖: ! 未提供关键词，跳过")

    if layout_warnings:
        print("9. 内容位置告警: ! 发现潜在问题")
        for issue in layout_warnings:
            print(f"   - {issue}")
    else:
        print("9. 内容位置告警: ✓ 未发现明显问题")

    critical_pass = all(
        [
            one_page,
            is_a4,
            has_text,
            no_html,
            sections_ok,
            contact_ok,
            bottom_margin_ok,
            (not args.keyword) or (not missing_keywords),
        ]
    )

    print("=" * 80)
    if critical_pass:
        print("最终结论: PASS")
        print("=" * 80)
        return 0

    print("最终结论: NEED-ADJUSTMENT")
    print("=" * 80)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
