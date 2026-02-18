#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout settings for resume PDF template."""

from __future__ import annotations

from dataclasses import dataclass

_COMPACT_FONT_SIZE_SCALE = 0.92
_COMPACT_LINE_HEIGHT_SCALE = 0.90
_COMPACT_SECTION_SPACING_SCALE = 0.80
_COMPACT_ITEM_SPACING_SCALE = 0.75

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

    @property
    def effective_font_size_scale(self) -> float:
        if self.compact_mode and self.font_size_scale == 1.0:
            return _COMPACT_FONT_SIZE_SCALE
        return _clamp(self.font_size_scale if self.font_size_scale is not None else 1.0)

    @property
    def effective_line_height_scale(self) -> float:
        if self.compact_mode and self.line_height_scale == 1.0:
            return _COMPACT_LINE_HEIGHT_SCALE
        return _clamp(
            self.line_height_scale if self.line_height_scale is not None else 1.0
        )

    @property
    def effective_section_spacing_scale(self) -> float:
        if self.compact_mode and self.section_spacing_scale == 1.0:
            return _COMPACT_SECTION_SPACING_SCALE
        return _clamp(
            self.section_spacing_scale
            if self.section_spacing_scale is not None
            else 1.0
        )

    @property
    def effective_item_spacing_scale(self) -> float:
        if self.compact_mode and self.item_spacing_scale == 1.0:
            return _COMPACT_ITEM_SPACING_SCALE
        return _clamp(
            self.item_spacing_scale if self.item_spacing_scale is not None else 1.0
        )


DEFAULT_SETTINGS = LayoutSettings()
