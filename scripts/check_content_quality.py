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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.resume_shared import (  # noqa: E402
    collect_bullets,
    load_json_file,
    starts_with_action_verb,
    validate_resume_content,
)

_MAX_BULLET_WORDS = 28
_VERB_PASS_THRESHOLD = 0.60
_NGRAM_REPEAT_THRESHOLD = 3


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
        if not starts_with_action_verb(b):
            words = b.split()
            first_word = words[0].lower().rstrip(".,;:") if words else ""
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


def check_bullet_density(experience: list[dict[str, Any]]) -> dict[str, str]:
    """Review experience density relative to the number of entries."""
    entry_count = len(experience)
    bullet_count = sum(len(entry.get("bullets", [])) for entry in experience)
    if entry_count == 0:
        return {
            "name": "bullet_density",
            "status": "PASS",
            "detail": "No experience entries to review",
        }
    minimum = max(3, entry_count * 2)
    maximum = entry_count * 6
    status = "PASS" if minimum <= bullet_count <= maximum else "WARN"
    return {
        "name": "bullet_density",
        "status": status,
        "detail": (
            f"{bullet_count} bullets across {entry_count} experience entries "
            f"(contextual range {minimum}-{maximum})"
        ),
    }


def run_all_checks(resume: dict[str, Any] | Path) -> list[dict[str, str]]:
    """Run all content quality checks on a resume dict or JSON file path."""
    if isinstance(resume, Path):
        resume = load_json_file(resume)
    validate_resume_content(resume, require_non_empty=True)
    all_bullets = collect_bullets(resume, include_projects=True)
    return [
        check_bullet_length(all_bullets),
        check_bullet_starts_with_verb(all_bullets),
        check_duplicate_phrases(all_bullets),
        check_bullet_density(resume.get("experience", [])),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Content quality checks for resume JSON")
    parser.add_argument("resume_json", help="Path to resume-working.json")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    resume_path = Path(args.resume_json).expanduser().resolve()
    try:
        results = run_all_checks(resume_path)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: content quality check failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        passed = sum(1 for r in results if r["status"] == "PASS")
        total = len(results)
        for r in results:
            icon = (
                "\u2713"
                if r["status"] == "PASS"
                else "\u26a0"
                if r["status"] == "WARN"
                else "\u2717"
            )
            print(f"  {icon} [{r['status']}] {r['name']}: {r['detail']}")
        print(f"\nContent QC: {passed}/{total} checks passed")

    return 0 if all(r["status"] == "PASS" for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
