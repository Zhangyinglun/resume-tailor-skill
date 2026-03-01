#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout settings for resume PDF template."""

from __future__ import annotations

from dataclasses import dataclass

_COMPACT_DEFAULTS = {
    "font_size": 0.92,
    "line_height": 0.88,
    "section_spacing": 0.88,
    "item_spacing": 0.85,
}

_MIN_SCALE = 0.7
_MAX_SCALE = 1.3


def _clamp(
    value: float, minimum: float = _MIN_SCALE, maximum: float = _MAX_SCALE
) -> float:
    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class LayoutSettings:
    """Immutable layout configuration for PDF generation."""

    font_size_scale: float | None = 1.0
    line_height_scale: float | None = 1.0
    section_spacing_scale: float | None = 1.0
    item_spacing_scale: float | None = 1.0
    margin_top_mm: float = 5.0
    margin_bottom_mm: float = 5.0
    margin_side_inch: float = 0.6
    compact_mode: bool = False

    def _effective(self, field: str) -> float:
        raw = getattr(self, f"{field}_scale")
        value = raw if raw is not None else 1.0
        if self.compact_mode and value == 1.0:
            return _COMPACT_DEFAULTS[field]
        return _clamp(value)

    @property
    def effective_font_size_scale(self) -> float:
        return self._effective("font_size")

    @property
    def effective_line_height_scale(self) -> float:
        return self._effective("line_height")

    @property
    def effective_section_spacing_scale(self) -> float:
        return self._effective("section_spacing")

    @property
    def effective_item_spacing_scale(self) -> float:
        return self._effective("item_spacing")


DEFAULT_SETTINGS = LayoutSettings()
