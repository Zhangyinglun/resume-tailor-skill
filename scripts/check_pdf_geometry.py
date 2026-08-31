#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect rendered PDF word coordinates for sparse bullet endings and content fit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.resume_shared import validate_resume_content  # noqa: E402

_BULLET_MARKERS = {"•", "·", "-", "(cid:127)"}

_SECTION_HEADERS: dict[str, str] = {
    "SUMMARY": "summary",
    "PROFESSIONAL SUMMARY": "summary",
    "PROFESSIONAL EXPERIENCE": "experience",
    "EXPERIENCE": "experience",
    "WORK EXPERIENCE": "experience",
    "PROJECTS": "projects",
    "PROJECT": "projects",
    "TECHNICAL SKILLS": "skills",
    "SKILLS": "skills",
    "AWARDS": "awards",
    "AWARD": "awards",
    "CERTIFICATIONS": "certifications",
    "CERTIFICATION": "certifications",
    "EDUCATION": "education",
}


def points_to_mm(value: float) -> float:
    return value * 25.4 / 72.0


def _word_coordinates(words: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Collect numeric word coordinates, skipping malformed entries."""
    coords: dict[str, list[float]] = {"top": [], "bottom": [], "x0": [], "x1": []}
    for word in words:
        for key in coords:
            try:
                coords[key].append(float(word[key]))
            except (KeyError, TypeError, ValueError):
                continue
    return coords


def estimate_page_margins_mm(page: Any) -> dict[str, float] | None:
    words = page.extract_words() or []
    if not words:
        return None

    coords = _word_coordinates(words)
    if not all(coords.values()):
        return None

    return {
        "top": points_to_mm(min(coords["top"])),
        "bottom": points_to_mm(page.height - max(coords["bottom"])),
        "left": points_to_mm(min(coords["x0"])),
        "right": points_to_mm(page.width - max(coords["x1"])),
    }


def extract_page_lines(page: Any, *, top_tolerance: float = 2.5) -> list[dict[str, Any]]:
    """Group pdfplumber words into rendered lines using their y coordinates."""
    words = sorted(
        (page.extract_words() or []),
        key=lambda word: (float(word.get("top", 0.0)), float(word.get("x0", 0.0))),
    )
    groups: list[list[dict[str, Any]]] = []
    for word in words:
        top = float(word.get("top", 0.0))
        if not groups:
            groups.append([word])
            continue
        group_top = sum(float(item.get("top", 0.0)) for item in groups[-1]) / len(groups[-1])
        if abs(top - group_top) <= top_tolerance:
            groups[-1].append(word)
        else:
            groups.append([word])

    lines: list[dict[str, Any]] = []
    for group in groups:
        ordered = sorted(group, key=lambda word: float(word.get("x0", 0.0)))
        texts = [str(word.get("text", "")).strip() for word in ordered]
        texts = [text for text in texts if text]
        if not texts:
            continue
        lines.append(
            {
                "text": " ".join(texts),
                "x0": min(float(word["x0"]) for word in ordered),
                "x1": max(float(word["x1"]) for word in ordered),
                "top": min(float(word["top"]) for word in ordered),
                "bottom": max(float(word["bottom"]) for word in ordered),
                "words": texts,
            }
        )
    return lines


def _starts_bullet(line: dict[str, Any]) -> bool:
    words = line.get("words", [])
    if not words:
        return False
    first = str(words[0]).strip()
    return first in _BULLET_MARKERS or first.startswith("•")


def _calc_geometry(sec_lines: list[dict[str, Any]]) -> dict[str, float | int]:
    if not sec_lines:
        return {"line_count": 0, "height_mm": 0.0}
    top_min = min(float(line["top"]) for line in sec_lines)
    bottom_max = max(float(line["bottom"]) for line in sec_lines)
    height_pt = max(0.0, bottom_max - top_min)
    return {
        "line_count": len(sec_lines),
        "height_mm": round(points_to_mm(height_pt), 1),
    }


def _match_experience_entries(
    lines: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> dict[str, dict[str, float | int]] | None:
    if not entries:
        return None

    start_indices: list[int] = []
    current_line_idx = 0

    for i, entry in enumerate(entries):
        company = str(entry.get("company", "")).strip().casefold()
        dates = str(entry.get("dates", "")).strip().casefold()
        title = str(entry.get("title", "")).strip().casefold()

        found_idx = None
        for idx in range(current_line_idx, len(lines)):
            line = lines[idx]
            if _starts_bullet(line):
                continue
            line_text = str(line.get("text", "")).casefold()

            company_match = bool(company and company in line_text)
            dates_match = bool(dates and dates in line_text)
            title_match = bool(title and title in line_text)

            if company_match:
                other_same_company = [
                    other
                    for j, other in enumerate(entries)
                    if j != i and str(other.get("company", "")).strip().casefold() == company
                ]
                if other_same_company:
                    if dates_match or title_match or idx == current_line_idx:
                        found_idx = idx
                        break
                else:
                    found_idx = idx
                    break
            elif dates_match and title_match:
                found_idx = idx
                break

        if found_idx is None:
            return None

        start_indices.append(found_idx)
        current_line_idx = found_idx + 1

    result: dict[str, dict[str, float | int]] = {}
    for i in range(len(entries)):
        start = 0 if i == 0 else start_indices[i]
        end = start_indices[i + 1] if i + 1 < len(entries) else len(lines)
        entry_lines = lines[start:end]
        result[f"experience[{i}]"] = _calc_geometry(entry_lines)
    return result


def _section_geometry(
    lines: list[dict[str, Any]],
    resume: dict[str, Any],
) -> dict[str, dict[str, float | int]]:
    """Group rendered PDF lines into section and entry geometry."""
    section_lines: dict[str, list[dict[str, Any]]] = {}
    current_section: str | None = None

    for line in lines:
        text = str(line.get("text", "")).strip()
        upper_text = text.upper()
        if upper_text in _SECTION_HEADERS:
            current_section = _SECTION_HEADERS[upper_text]
            if current_section not in section_lines:
                section_lines[current_section] = []
            continue
        if current_section is not None:
            section_lines[current_section].append(line)

    result: dict[str, dict[str, float | int]] = {}
    for section_name, sec_lines in section_lines.items():
        if section_name == "experience":
            entries = resume.get("experience")
            if isinstance(entries, list) and entries:
                matched = _match_experience_entries(sec_lines, entries)
                if matched is not None:
                    result.update(matched)
                    continue
            result["experience"] = _calc_geometry(sec_lines)
        else:
            result[section_name] = _calc_geometry(sec_lines)

    return result


def detect_sparse_bullet_endings(
    lines: list[dict[str, Any]],
    *,
    page_width: float,
    max_words: int = 3,
    min_fill_ratio: float = 0.35,
) -> list[dict[str, Any]]:
    """Detect 1–3 word trailing lines using actual rendered coordinates."""
    findings: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        first = lines[index]
        if not _starts_bullet(first):
            index += 1
            continue
        paragraph = [first]
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            previous = paragraph[-1]
            if _starts_bullet(candidate):
                break
            line_height = max(1.0, float(previous["bottom"]) - float(previous["top"]))
            vertical_gap = float(candidate["top"]) - float(previous["top"])
            is_continuation = (
                vertical_gap <= max(14.0, line_height * 1.8)
                and float(candidate["x0"]) >= float(first["x0"]) + 2.0
            )
            if not is_continuation:
                break
            paragraph.append(candidate)
            cursor += 1

        if len(paragraph) > 1:
            trailing = paragraph[-1]
            word_count = len(trailing.get("words", []))
            usable_width = max(
                1.0,
                min(page_width, float(first["x1"])) - float(trailing["x0"]),
            )
            occupied_width = max(0.0, float(trailing["x1"]) - float(trailing["x0"]))
            fill_ratio = occupied_width / usable_width
            if word_count <= max_words and fill_ratio < min_fill_ratio:
                findings.append(
                    {
                        "text": str(trailing["text"]),
                        "word_count": word_count,
                        "fill_ratio": round(fill_ratio, 3),
                        "top": round(float(trailing["top"]), 2),
                    }
                )
        index = max(index + 1, cursor)
    return findings


def check_pdf_geometry(pdf_path: Path) -> dict[str, Any]:
    """Return page-level sparse trailing-line findings from a rendered PDF."""
    page_reports: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            findings = detect_sparse_bullet_endings(
                extract_page_lines(page),
                page_width=float(page.width),
            )
            page_reports.append(
                {"page": page_number, "sparse_trailing_lines": findings}
            )
    total = sum(len(page["sparse_trailing_lines"]) for page in page_reports)
    return {
        "verdict": "PASS" if total == 0 else "NEED-ADJUSTMENT",
        "sparse_trailing_line_count": total,
        "pages": page_reports,
    }


def build_content_fit_feedback(
    pdf_path: Path,
    resume: dict[str, Any],
    *,
    plan_revision: int,
    preferred_max_bottom_mm: float = 8.0,
) -> dict[str, Any]:
    """Generate real PDF content fit feedback against the preferred layout."""
    validate_resume_content(resume, require_non_empty=True)
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        if page_count == 0:
            raise ValueError(f"PDF contains no pages: {pdf_path}")
        page_lines = [extract_page_lines(page) for page in pdf.pages]
        first_page = pdf.pages[0]
        margins = estimate_page_margins_mm(first_page)
        section_geometry = _section_geometry(page_lines[0], resume)
        sparse = detect_sparse_bullet_endings(
            page_lines[0], page_width=float(first_page.width)
        )

    skills_lines = int(section_geometry.get("skills", {}).get("line_count", 0))
    issues: list[str] = []
    if skills_lines and not (2 <= skills_lines <= 4):
        issues.append("skills_rendered_line_budget")
    if page_count > 1:
        verdict = "overflow"
    elif margins is not None and margins["bottom"] > preferred_max_bottom_mm:
        verdict = "underfill"
    elif issues:
        verdict = "revision_required"
    else:
        verdict = "fit"
    return {
        "schema_version": 1,
        "plan_revision": plan_revision,
        "verdict": verdict,
        "page_count": page_count,
        "bottom_whitespace_mm": None if margins is None else round(margins["bottom"], 2),
        "section_geometry": section_geometry,
        "sparse_trailing_bullets": sparse,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check rendered PDF line geometry.")
    parser.add_argument("pdf_path", help="PDF file path")
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to resume JSON to evaluate content fit feedback",
    )
    parser.add_argument(
        "--plan-revision",
        type=int,
        default=1,
        help="Plan revision number (default: 1)",
    )
    parser.add_argument(
        "--preferred-max-bottom-mm",
        type=float,
        default=8.0,
        help="Preferred maximum bottom whitespace in mm (default: 8.0)",
    )
    parser.add_argument(
        "--feedback-output",
        type=str,
        default=None,
        help="Path to write content fit feedback JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    args = parser.parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        print(f"Error: File does not exist: {pdf_path}", file=sys.stderr)
        return 1

    if args.resume:
        resume_path = Path(args.resume).expanduser().resolve()
        if not resume_path.exists():
            print(f"Error: Resume file does not exist: {resume_path}", file=sys.stderr)
            return 1
        try:
            resume = json.loads(resume_path.read_text(encoding="utf-8"))
            feedback = build_content_fit_feedback(
                pdf_path,
                resume,
                plan_revision=args.plan_revision,
                preferred_max_bottom_mm=args.preferred_max_bottom_mm,
            )
        except Exception as exc:  # noqa: BLE001 - stable failure exit
            print(f"Error: Content fit check failed: {exc}", file=sys.stderr)
            return 1

        if args.feedback_output:
            out_path = Path(args.feedback_output).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(feedback, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if args.json_output:
            print(json.dumps(feedback, ensure_ascii=False, indent=2))
        else:
            print(
                f"Content fit: {feedback['verdict']} "
                f"(page_count={feedback['page_count']}, "
                f"bottom_whitespace={feedback['bottom_whitespace_mm']}mm)"
            )
            if feedback["issues"]:
                print(f"  Issues: {', '.join(feedback['issues'])}")
            if feedback["sparse_trailing_bullets"]:
                print(f"  Sparse trailing bullets: {len(feedback['sparse_trailing_bullets'])}")

        return 0 if feedback["verdict"] == "fit" else 2

    try:
        report = check_pdf_geometry(pdf_path)
    except Exception as exc:  # noqa: BLE001 - CLI exposes a stable failure code.
        print(f"Error: PDF geometry check failed: {exc}", file=sys.stderr)
        return 1
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"PDF geometry: {report['verdict']}")
        for page in report["pages"]:
            for finding in page["sparse_trailing_lines"]:
                print(
                    f"  ⚠ page {page['page']}: {finding['word_count']} word(s), "
                    f"fill={finding['fill_ratio']:.0%}: {finding['text']}"
                )
    return 0 if report["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

