"""Tests for check_content_quality.py — bullet line fill check and pdf quality defaults."""
import pytest
from scripts.check_content_quality import check_bullet_line_fill
from scripts.check_pdf_quality import DEFAULT_MARGIN_THRESHOLDS


# ---------------------------------------------------------------------------
# check_bullet_line_fill
# ---------------------------------------------------------------------------

def test_empty_bullets_passes():
    result = check_bullet_line_fill([])
    assert result["status"] == "PASS"


def test_single_line_bullet_passes():
    # 95 chars or fewer — does not wrap, must PASS regardless of content
    short_bullet = "A" * 94
    result = check_bullet_line_fill([short_bullet])
    assert result["status"] == "PASS"


def test_wrapping_bullet_with_good_fill():
    # len = 95 * 1 + 48 = 143  →  remainder 48 >= 95*0.5=47.5  → PASS
    good_bullet = "A" * (95 + 48)
    result = check_bullet_line_fill([good_bullet])
    assert result["status"] == "PASS"


def test_wrapping_bullet_with_sparse_fill():
    # len = 95 + 10 = 105  →  remainder 10 < 95*0.5=47.5  → WARN
    sparse_bullet = "A" * (95 + 10)
    result = check_bullet_line_fill([sparse_bullet])
    assert result["status"] == "WARN"


def test_mixed_bullets_flags_only_sparse():
    good_bullet = "A" * (95 + 48)   # passes
    sparse_bullet = "A" * (95 + 10)  # fails
    result = check_bullet_line_fill([good_bullet, sparse_bullet])
    assert result["status"] == "WARN"
    assert "1" in result["detail"]  # 1 offending bullet


# ---------------------------------------------------------------------------
# DEFAULT_MARGIN_THRESHOLDS
# ---------------------------------------------------------------------------

def test_max_bottom_mm_is_8():
    assert DEFAULT_MARGIN_THRESHOLDS["max_bottom_mm"] == 8.0
