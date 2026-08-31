#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect rendered PDF word coordinates for sparse bullet endings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pdfplumber

_BULLET_MARKERS = {"•", "·", "-", "(cid:127)"}


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check rendered PDF line geometry.")
    parser.add_argument("pdf_path", help="PDF file path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        print(f"Error: File does not exist: {pdf_path}", file=sys.stderr)
        return 1
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
