#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automatic layout tuning for one-page resume generation."""

from __future__ import annotations

import json
import subprocess
import tempfile
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

from templates.layout_settings import LayoutSettings
from templates.modern_resume_template import generate_resume

# Checks that layout tuning can potentially fix (margins, page overflow).
LAYOUT_FIXABLE_CHECKS = {"page_count", "bottom_margin", "top_margin", "side_margins"}

# Checks that require content changes — layout tuning cannot fix these.
CONTENT_CHECKS = {
    "page_size", "text_layer", "html_leak", "placeholder_content",
    "section_completeness", "contact_info", "keyword_coverage",
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


def _scales(layout: LayoutSettings) -> tuple[float, float, float, float]:
    """Extract the four effective scale values."""
    return (
        layout.effective_font_size_scale,
        layout.effective_line_height_scale,
        layout.effective_section_spacing_scale,
        layout.effective_item_spacing_scale,
    )


def _shrink_candidates() -> list[LayoutSettings]:
    """Presets that progressively reduce layout params for overflowing content.

    4-phase strategy: line_height first → font+line → compact deep → margins last.
    """
    return [
        # Phase A: pure line-height compression (lowest visual cost)
        LayoutSettings(line_height_scale=0.95),
        LayoutSettings(line_height_scale=0.92),
        LayoutSettings(line_height_scale=0.90),
        LayoutSettings(line_height_scale=0.88),
        # Phase B: line-height + font, spacing follows proportionally
        LayoutSettings(font_size_scale=0.97, line_height_scale=0.92,
                        section_spacing_scale=0.95, item_spacing_scale=0.93),
        LayoutSettings(font_size_scale=0.95, line_height_scale=0.90,
                        section_spacing_scale=0.92, item_spacing_scale=0.90),
        LayoutSettings(font_size_scale=0.93, line_height_scale=0.88,
                        section_spacing_scale=0.90, item_spacing_scale=0.87),
        # Phase C: compact_mode + progressive deep compression
        LayoutSettings(compact_mode=True),
        LayoutSettings(compact_mode=True, font_size_scale=0.90, line_height_scale=0.86,
                        section_spacing_scale=0.86, item_spacing_scale=0.82),
        LayoutSettings(compact_mode=True, font_size_scale=0.88, line_height_scale=0.84,
                        section_spacing_scale=0.84, item_spacing_scale=0.80),
        LayoutSettings(compact_mode=True, font_size_scale=0.86, line_height_scale=0.82,
                        section_spacing_scale=0.82, item_spacing_scale=0.78),
        # Phase D: compact + margin tightening (last resort)
        LayoutSettings(compact_mode=True, font_size_scale=0.90, line_height_scale=0.86,
                        section_spacing_scale=0.86, item_spacing_scale=0.83,
                        margin_top_mm=4.5, margin_bottom_mm=4.5),
        LayoutSettings(compact_mode=True, font_size_scale=0.88, line_height_scale=0.84,
                        section_spacing_scale=0.82, item_spacing_scale=0.80,
                        margin_top_mm=4.2, margin_bottom_mm=4.2),
        LayoutSettings(compact_mode=True, font_size_scale=0.86, line_height_scale=0.82,
                        section_spacing_scale=0.80, item_spacing_scale=0.76,
                        margin_top_mm=4.0, margin_bottom_mm=4.0),
        LayoutSettings(compact_mode=True, font_size_scale=0.84, line_height_scale=0.80,
                        section_spacing_scale=0.78, item_spacing_scale=0.74,
                        margin_top_mm=4.0, margin_bottom_mm=4.0, margin_side_inch=0.55),
    ]


def _expand_candidates() -> list[LayoutSettings]:
    """Presets that progressively increase font/spacing for sparse content."""
    return [
        LayoutSettings(font_size_scale=1.01, line_height_scale=1.02,
                        section_spacing_scale=1.02, item_spacing_scale=1.02),
        LayoutSettings(font_size_scale=1.02, line_height_scale=1.03,
                        section_spacing_scale=1.04, item_spacing_scale=1.04),
        LayoutSettings(font_size_scale=1.03, line_height_scale=1.04,
                        section_spacing_scale=1.06, item_spacing_scale=1.06),
        LayoutSettings(font_size_scale=1.04, line_height_scale=1.05,
                        section_spacing_scale=1.08, item_spacing_scale=1.08),
        LayoutSettings(font_size_scale=1.05, line_height_scale=1.05),
        LayoutSettings(font_size_scale=1.08, line_height_scale=1.08,
                        section_spacing_scale=1.10, item_spacing_scale=1.10),
        LayoutSettings(font_size_scale=1.10, line_height_scale=1.12,
                        section_spacing_scale=1.15, item_spacing_scale=1.15),
        LayoutSettings(font_size_scale=1.15, line_height_scale=1.15,
                        section_spacing_scale=1.20, item_spacing_scale=1.20),
        LayoutSettings(font_size_scale=1.20, line_height_scale=1.20,
                        section_spacing_scale=1.25, item_spacing_scale=1.25,
                        margin_top_mm=6.0, margin_bottom_mm=6.0),
    ]


def _failed_checks(report: dict[str, Any]) -> set[str]:
    return {
        c["name"] for c in report.get("checks", [])
        if isinstance(c.get("name"), str) and c.get("passed") is False
    }


def _diagnose_direction(report: dict[str, Any]) -> str:
    """Return ``'shrink'``, ``'expand'``, or ``'pass'`` based on QC failures."""
    checks = {c["name"]: c for c in report.get("checks", [])}

    page_count = checks.get("page_count", {}).get("detail", {}).get("count", 1)
    if page_count > 1:
        return "shrink"

    bottom = checks.get("bottom_margin", {})
    bottom_mm = bottom.get("detail", {}).get("bottom_mm")
    if bottom_mm is not None and bottom.get("passed") is False:
        return "expand" if bottom_mm > 8.0 else "shrink"

    if _failed_checks(report) & LAYOUT_FIXABLE_CHECKS:
        return "shrink"

    return "pass"


def _build_candidates(
    max_trials: int, *, hint: LayoutSettings | None = None, direction: str = "shrink",
) -> list[LayoutSettings]:
    """Build candidate list based on diagnosed direction and optional hint."""
    default = LayoutSettings(compact_mode=False)
    presets = [default] + (_expand_candidates() if direction == "expand" else _shrink_candidates())

    if hint is not None and hint not in presets:
        presets.insert(0, hint)

    return presets[: max(1, max_trials)]


def _readability_score(layout: LayoutSettings) -> float:
    fs, lh, ss, it = _scales(layout)
    return fs * 0.45 + lh * 0.30 + ss * 0.15 + it * 0.10


def _compression_distance(layout: LayoutSettings) -> float:
    return sum(abs(1.0 - v) for v in _scales(layout))


def score_trial(trial: AutoFitTrial) -> tuple[int, int, int, float, float]:
    """Score trial; higher tuple is better.

    Priority: pass > fewer layout failures > fewer total > closer to default > higher readability.
    """
    failed = _failed_checks(trial.report)
    return (
        1 if trial.report.get("verdict") == "PASS" else 0,
        -len(failed & LAYOUT_FIXABLE_CHECKS),
        -len(failed),
        -_compression_distance(trial.layout),
        _readability_score(trial.layout),
    )


def _run_quality_check(pdf_path: Path) -> dict[str, Any]:
    script = Path(__file__).resolve().parent / "check_pdf_quality.py"
    result = subprocess.run(
        ["python3", str(script), str(pdf_path), "--json"],
        capture_output=True, text=True, check=False,
    )
    if not result.stdout.strip():
        raise ValueError(f"Quality checker returned empty output: {result.stderr}")
    return json.loads(result.stdout.strip())


def _run_trial(content: dict[str, Any], output_file: str, layout: LayoutSettings, trial_dir: Path) -> AutoFitTrial:
    """Generate PDF and run quality check for a single layout candidate."""
    trial_dir.mkdir(parents=True, exist_ok=True)
    with redirect_stdout(StringIO()):
        generated = generate_resume(output_file, content, base_dir=str(trial_dir), layout=layout)
    return AutoFitTrial(layout=layout, report=_run_quality_check(Path(generated)))


def auto_fit_layout(
    content: dict[str, Any],
    *, output_file: str, max_trials: int,
    hint_layout: LayoutSettings | None = None,
) -> AutoFitResult:
    """Try multiple layout presets and return the best trial."""
    with tempfile.TemporaryDirectory(prefix="resume-autofit-") as temp_dir:
        base_temp = Path(temp_dir)

        # Phase 1: Diagnostic pass
        first_layout = hint_layout or LayoutSettings()
        first_trial = _run_trial(content, output_file, first_layout, base_temp / "trial-1")

        direction = _diagnose_direction(first_trial.report)
        if direction == "pass":
            return AutoFitResult(best_layout=first_trial.layout, best_report=first_trial.report, trials_run=1)

        # Phase 2: Directional candidates
        candidates = [c for c in _build_candidates(max_trials - 1, hint=hint_layout, direction=direction)
                      if c != first_layout]

        trials = [first_trial] + [
            _run_trial(content, output_file, layout, base_temp / f"trial-{i}")
            for i, layout in enumerate(candidates, start=2)
        ]

    best = max(trials, key=score_trial)
    return AutoFitResult(best_layout=best.layout, best_report=best.report, trials_run=len(trials))
