"""Tests for JD analysis save/show functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from scripts.resume_cache_manager import (
    JD_ANALYSIS_REL_PATH,
    read_jd_analysis,
    reset_cache_on_start,
    save_jd_analysis,
    validate_jd_analysis,
)


def _valid_payload() -> dict:
    return {
        "position": "Senior Software Engineer",
        "keywords": {
            "P1": ["Python", "distributed systems"],
            "P2": ["AWS", "Kubernetes"],
            "P3": ["GraphQL"],
        },
        "alignment": {
            "matched": ["Python", "AWS"],
            "gaps": ["Kubernetes"],
        },
    }


class TestValidateJdAnalysis:
    """Tests for validate_jd_analysis."""

    def test_valid_payload_passes(self) -> None:
        validate_jd_analysis(_valid_payload())

    def test_missing_top_level_keys_raises(self) -> None:
        for key in ("position", "keywords", "alignment"):
            payload = _valid_payload()
            del payload[key]
            with pytest.raises(ValueError, match="missing required fields"):
                validate_jd_analysis(payload)

    def test_missing_keyword_tiers_raises(self) -> None:
        for tier in ("P1", "P2", "P3"):
            payload = _valid_payload()
            del payload["keywords"][tier]
            with pytest.raises(ValueError, match="missing required tiers"):
                validate_jd_analysis(payload)

    def test_non_list_keyword_tier_raises(self) -> None:
        payload = _valid_payload()
        payload["keywords"]["P1"] = "not a list"
        with pytest.raises(ValueError, match=r"keywords\.P1 must be an array"):
            validate_jd_analysis(payload)

    def test_keywords_not_dict_raises(self) -> None:
        payload = _valid_payload()
        payload["keywords"] = "bad"
        with pytest.raises(ValueError, match="`keywords` must be an object"):
            validate_jd_analysis(payload)

    def test_alignment_not_dict_raises(self) -> None:
        payload = _valid_payload()
        payload["alignment"] = []
        with pytest.raises(ValueError, match="`alignment` must be an object"):
            validate_jd_analysis(payload)

    def test_missing_alignment_fields_raises(self) -> None:
        for field in ("matched", "gaps"):
            payload = _valid_payload()
            del payload["alignment"][field]
            with pytest.raises(ValueError, match="alignment missing required field"):
                validate_jd_analysis(payload)

    def test_alignment_field_not_list_raises(self) -> None:
        payload = _valid_payload()
        payload["alignment"]["matched"] = "not a list"
        with pytest.raises(ValueError, match=r"alignment\.matched must be an array"):
            validate_jd_analysis(payload)


class TestSaveAndReadJdAnalysis:
    """Tests for save_jd_analysis and read_jd_analysis round-trip."""

    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "cache").mkdir()
            payload = _valid_payload()
            path = save_jd_analysis(workspace, payload)
            assert path.exists()
            result = read_jd_analysis(workspace)
            assert result == payload

    def test_save_invalid_payload_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "cache").mkdir()
            with pytest.raises(ValueError):
                save_jd_analysis(workspace, {"position": "X"})

    def test_read_missing_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with pytest.raises(FileNotFoundError):
                read_jd_analysis(workspace)


class TestResetCleansJdAnalysis:
    """Test that reset_cache_on_start also removes jd-analysis.json."""

    def test_reset_deletes_jd_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            jd_path = workspace / JD_ANALYSIS_REL_PATH
            jd_path.parent.mkdir(parents=True, exist_ok=True)
            jd_path.write_text("{}", encoding="utf-8")
            assert jd_path.exists()
            reset_cache_on_start(workspace)
            assert not jd_path.exists()
