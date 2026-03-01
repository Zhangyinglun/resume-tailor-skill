#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Centralized design tokens for resume PDF template."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    """Immutable design constants for the resume template.

    All font sizes, leading values, and spacing are BASE values before
    LayoutSettings scaling is applied.
    """

    # -- Colors (RGB 0-255) --
    accent_color: tuple[int, int, int] = (0x2B, 0x3A, 0x4E)
    body_ink_color: tuple[int, int, int] = (0x1A, 0x1A, 0x2E)

    # -- Font sizes (pt) --
    header_font_size: float = 15.0
    contact_font_size: float = 10.5
    section_font_size: float = 10.6
    body_font_size: float = 9.85
    company_font_size: float = 10.2
    dates_font_size: float = 9.9
    job_detail_font_size: float = 9.9
    bullet_font_size: float = 9.85
    education_font_size: float = 9.9

    # -- Leading (pt) --
    header_leading: float = 20.0   # 15pt font needs ~20pt leading for descender clearance
    section_leading: float = 13.0
    body_leading: float = 12.2
    company_leading: float = 12.5
    dates_leading: float = 12.0
    job_detail_leading: float = 12.0
    bullet_leading: float = 12.2
    education_leading: float = 12.0

    # -- Spacing (pt, before LayoutSettings scaling) --
    header_space_after: float = 4.0
    contact_space_after: float = 2.0
    section_space_before: float = 8.5
    section_space_after: float = 5.0
    body_space_after: float = 6.2
    company_space_after: float = 2.5
    job_detail_space_after: float = 4.5
    bullet_space_after: float = 3.2
    education_space_after: float = 3.5

    # -- Bullet indentation (pt) --
    bullet_left_indent: float = 15.0
    bullet_indent: float = 5.0

    # -- Horizontal rules --
    section_hr_thickness: float = 0.6
    header_hr_thickness: float = 0.8
    header_hr_width: str = "30%"
    header_hr_space_after: float = 6.0


DEFAULT_TOKENS = DesignTokens()
