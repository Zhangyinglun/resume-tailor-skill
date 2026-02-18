#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automatic layout tuning for one-page resume generation."""

from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from templates.layout_settings import LayoutSettings
from templates.modern_resume_template import generate_resume

_CRITICAL_CHECKS = {
    "page_count",
    "page_size",
    "text_layer",
    "html_leak",
    "placeholder_content",
    "bottom_margin",
    "top_margin",
    "side_margins",
    "section_completeness",
    "contact_info",
    "keyword_coverage",
}


@dataclass(frozen=True)
class AutoFitTrial:
    """Single trial result for a layout candidate."""

    layout: LayoutSettings
    report: dict[str, Any]


@dataclass(frozen=True)
class AutoFitResult:
    """Best result selected from auto-fit trials."""

    best_layout: LayoutSettings
    best_report: dict[str, Any]
    trials_run: int


def _build_candidates(max_trials: int) -> list[LayoutSettings]:
    presets = [
        LayoutSettings(compact_mode=False),
        LayoutSettings(compact_mode=True),
        LayoutSettings(compact_mode=True, font_size_scale=0.90),
        LayoutSettings(compact_mode=True, font_size_scale=0.90, line_height_scale=0.88),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.88,
            line_height_scale=0.86,
            section_spacing_scale=0.82,
            item_spacing_scale=0.78,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.86,
            line_height_scale=0.84,
            section_spacing_scale=0.78,
            item_spacing_scale=0.74,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.84,
            line_height_scale=0.82,
            section_spacing_scale=0.75,
            item_spacing_scale=0.70,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.92,
            line_height_scale=0.90,
            section_spacing_scale=0.84,
            item_spacing_scale=0.80,
            margin_top_mm=4.5,
            margin_bottom_mm=4.5,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.90,
            line_height_scale=0.88,
            section_spacing_scale=0.80,
            item_spacing_scale=0.76,
            margin_top_mm=4.2,
            margin_bottom_mm=4.2,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.88,
            line_height_scale=0.84,
            section_spacing_scale=0.76,
            item_spacing_scale=0.72,
            margin_top_mm=4.0,
            margin_bottom_mm=4.0,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.86,
            line_height_scale=0.82,
            section_spacing_scale=0.74,
            item_spacing_scale=0.70,
            margin_top_mm=4.0,
            margin_bottom_mm=4.0,
            margin_side_inch=0.55,
        ),
        LayoutSettings(
            compact_mode=True,
            font_size_scale=0.84,
            line_height_scale=0.80,
            section_spacing_scale=0.72,
            item_spacing_scale=0.68,
            margin_top_mm=4.0,
            margin_bottom_mm=4.0,
            margin_side_inch=0.55,
        ),
    ]
    return presets[: max(1, max_trials)]


def _failed_checks(report: dict[str, Any]) -> set[str]:
    failed: set[str] = set()
    checks = report.get("checks", [])
    for check in checks:
        name = check.get("name")
        passed = check.get("passed")
        if isinstance(name, str) and passed is False:
            failed.add(name)
    return failed


def _readability_score(layout: LayoutSettings) -> float:
    fs = layout.effective_font_size_scale
    lh = layout.effective_line_height_scale
    ss = layout.effective_section_spacing_scale
    it = layout.effective_item_spacing_scale
    return fs * 0.5 + lh * 0.25 + ss * 0.15 + it * 0.1


def _compression_distance(layout: LayoutSettings) -> float:
    fs = layout.effective_font_size_scale
    lh = layout.effective_line_height_scale
    ss = layout.effective_section_spacing_scale
    it = layout.effective_item_spacing_scale
    return abs(1.0 - fs) + abs(1.0 - lh) + abs(1.0 - ss) + abs(1.0 - it)


def score_trial(trial: AutoFitTrial) -> tuple[int, int, int, float, float]:
    """Score trial; higher tuple is better."""

    failed = _failed_checks(trial.report)
    critical_failed = len(failed & _CRITICAL_CHECKS)
    total_failed = len(failed)
    passed = trial.report.get("verdict") == "PASS"
    return (
        1 if passed else 0,
        -critical_failed,
        -total_failed,
        _readability_score(trial.layout),
        -_compression_distance(trial.layout),
    )


def _run_quality_check(pdf_path: Path) -> dict[str, Any]:
    script_path = Path(__file__).resolve().parent / "check_pdf_quality.py"
    cmd = [
        "python3",
        str(script_path),
        str(pdf_path),
        "--json",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)

    output = completed.stdout.strip()
    if not output:
        raise ValueError(f"Quality checker returned empty output: {completed.stderr}")

    return json.loads(output)


def auto_fit_layout(
    content: dict[str, Any],
    *,
    output_file: str,
    max_trials: int,
) -> AutoFitResult:
    """Try multiple layout presets and return the best trial."""

    candidates = _build_candidates(max_trials)
    trials: list[AutoFitTrial] = []

    with tempfile.TemporaryDirectory(prefix="resume-autofit-") as temp_dir:
        base_temp = Path(temp_dir)

        for index, layout in enumerate(candidates, start=1):
            trial_dir = base_temp / f"trial-{index}"
            trial_dir.mkdir(parents=True, exist_ok=True)

            with redirect_stdout(StringIO()):
                generated_path = generate_resume(
                    output_file,
                    content,
                    base_dir=str(trial_dir),
                    layout=layout,
                )
            report = _run_quality_check(Path(generated_path))
            trials.append(AutoFitTrial(layout=layout, report=report))

    best = max(trials, key=score_trial)
    return AutoFitResult(
        best_layout=best.layout,
        best_report=best.report,
        trials_run=len(trials),
    )
