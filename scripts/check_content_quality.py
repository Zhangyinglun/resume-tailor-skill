#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Content-level quality checks for resume JSON data."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.resume_shared import _DIGIT_RE, collect_bullets, load_json_file

STRONG_VERBS: set[str] = {
    "achieved", "built", "created", "delivered", "designed",
    "developed", "drove", "enabled", "engineered", "established",
    "executed", "expanded", "generated", "grew", "headed",
    "identified", "implemented", "improved", "increased", "initiated",
    "integrated", "introduced", "launched", "led", "managed",
    "migrated", "modernized", "optimized", "orchestrated", "overhauled",
    "pioneered", "proposed", "reduced", "redesigned", "refactored",
    "resolved", "revamped", "scaled", "secured", "simplified",
    "spearheaded", "standardized", "streamlined", "strengthened",
    "supervised", "transformed", "unified", "upgraded",
    "accelerated", "automated",
}

_MAX_BULLET_WORDS = 28
_VERB_PASS_THRESHOLD = 0.60
_QUANT_WARN_THRESHOLD = 0.40
_QUANT_GOOD_THRESHOLD = 0.60
_NGRAM_REPEAT_THRESHOLD = 3
_EXP_BULLET_MIN = 8
_EXP_BULLET_MAX = 14


def check_bullet_length(bullets: list[str]) -> dict[str, str]:
    """Check that all bullets are at most 28 words."""
    long: list[str] = []
    for b in bullets:
        word_count = len(b.split())
        if word_count > _MAX_BULLET_WORDS:
            long.append(f"({word_count}w) {b[:80]}")
    if long:
        return {
            "name": "bullet_length",
            "status": "WARN",
            "detail": f"{len(long)} bullet(s) exceed {_MAX_BULLET_WORDS} words: {'; '.join(long)}",
        }
    return {
        "name": "bullet_length",
        "status": "PASS",
        "detail": f"All {len(bullets)} bullets are within {_MAX_BULLET_WORDS} words",
    }


def check_bullet_starts_with_verb(bullets: list[str]) -> dict[str, str]:
    """Check that bullets start with a strong action verb."""
    if not bullets:
        return {"name": "bullet_verb_start", "status": "PASS", "detail": "No bullets to check"}
    weak: list[str] = []
    for b in bullets:
        words = b.split()
        first_word = words[0].lower().rstrip(".,;:") if words else ""
        if first_word not in STRONG_VERBS:
            weak.append(f"{first_word}: {b[:60]}")
    ratio = 1.0 - len(weak) / len(bullets) if bullets else 1.0
    if ratio < _VERB_PASS_THRESHOLD:
        return {
            "name": "bullet_verb_start",
            "status": "WARN",
            "detail": (
                f"{len(weak)}/{len(bullets)} bullets ({100 - ratio * 100:.0f}%) "
                f"do not start with a strong verb"
            ),
        }
    return {
        "name": "bullet_verb_start",
        "status": "PASS",
        "detail": f"{len(bullets) - len(weak)}/{len(bullets)} bullets ({ratio * 100:.0f}%) start with a strong verb",
    }


def check_quantification_ratio(bullets: list[str]) -> dict[str, str]:
    """Check ratio of bullets containing numeric data."""
    if not bullets:
        return {"name": "quantification_ratio", "status": "PASS", "detail": "No bullets to check"}
    with_numbers = sum(1 for b in bullets if _DIGIT_RE.search(b))
    ratio = with_numbers / len(bullets)
    if ratio < _QUANT_WARN_THRESHOLD:
        return {
            "name": "quantification_ratio",
            "status": "WARN",
            "detail": f"{with_numbers}/{len(bullets)} ({ratio * 100:.0f}%) bullets contain numbers (target >= 40%)",
        }
    if ratio < _QUANT_GOOD_THRESHOLD:
        return {
            "name": "quantification_ratio",
            "status": "PASS",
            "detail": f"{with_numbers}/{len(bullets)} ({ratio * 100:.0f}%) bullets contain numbers (could improve to 60%+)",
        }
    return {
        "name": "quantification_ratio",
        "status": "PASS",
        "detail": f"{with_numbers}/{len(bullets)} ({ratio * 100:.0f}%) bullets contain numbers",
    }


def check_duplicate_phrases(bullets: list[str]) -> dict[str, str]:
    """Detect repeated 3-grams across all bullets."""
    counter: Counter[tuple[str, ...]] = Counter()
    for b in bullets:
        words = b.lower().split()
        for i in range(len(words) - 2):
            trigram = tuple(words[i : i + 3])
            counter[trigram] += 1
    repeated = {" ".join(ng): cnt for ng, cnt in counter.items() if cnt >= _NGRAM_REPEAT_THRESHOLD}
    if repeated:
        phrases = ", ".join(f'"{p}" (x{c})' for p, c in sorted(repeated.items()))
        return {
            "name": "duplicate_phrases",
            "status": "WARN",
            "detail": f"Repeated 3-grams found: {phrases}",
        }
    return {
        "name": "duplicate_phrases",
        "status": "PASS",
        "detail": "No 3-gram appears 3+ times",
    }


def check_bullet_count(exp_bullets: list[str]) -> dict[str, str]:
    """Check that experience bullet count is within 8-14."""
    count = len(exp_bullets)
    if _EXP_BULLET_MIN <= count <= _EXP_BULLET_MAX:
        return {
            "name": "bullet_count",
            "status": "PASS",
            "detail": f"{count} experience bullets (target {_EXP_BULLET_MIN}-{_EXP_BULLET_MAX})",
        }
    return {
        "name": "bullet_count",
        "status": "WARN",
        "detail": f"{count} experience bullets (target {_EXP_BULLET_MIN}-{_EXP_BULLET_MAX})",
    }


def run_all_checks(resume_path: Path, jd_path: Path | None = None) -> list[dict[str, str]]:
    """Run all content quality checks."""
    resume = load_json_file(resume_path)
    # jd_path reserved for future keyword density check (Task 6)

    all_bullets = collect_bullets(resume, include_projects=True)
    exp_bullets = collect_bullets(resume, include_projects=False)

    return [
        check_bullet_length(all_bullets),
        check_bullet_starts_with_verb(all_bullets),
        check_quantification_ratio(all_bullets),
        check_duplicate_phrases(all_bullets),
        check_bullet_count(exp_bullets),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Content quality checks for resume JSON")
    parser.add_argument("resume_json", help="Path to resume-working.json")
    parser.add_argument("--jd-json", help="Path to jd-analysis.json (optional)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    resume_path = Path(args.resume_json).expanduser().resolve()
    jd_path = Path(args.jd_json).expanduser().resolve() if args.jd_json else None

    results = run_all_checks(resume_path, jd_path)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        passed = sum(1 for r in results if r["status"] == "PASS")
        total = len(results)
        for r in results:
            icon = "\u2713" if r["status"] == "PASS" else "\u26a0" if r["status"] == "WARN" else "\u2717"
            print(f"  {icon} [{r['status']}] {r['name']}: {r['detail']}")
        print(f"\nContent QC: {passed}/{total} checks passed")

    return 0 if all(r["status"] != "FAIL" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
