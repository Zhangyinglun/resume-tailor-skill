"""Tests for nested field validation in validate_resume_content()."""

from __future__ import annotations

import copy

import pytest

from scripts.resume_shared import validate_resume_content

_VALID_PAYLOAD: dict = {
    "name": "Jane Doe",
    "contact": "jane@example.com",
    "summary": "Software engineer.",
    "skills": [
        {"category": "Languages", "items": "Python, Go"},
    ],
    "experience": [
        {
            "company": "Acme Corp",
            "title": "Engineer",
            "dates": "2020 - Present",
            "bullets": ["Built services.", "Reduced latency."],
        },
    ],
    "education": [
        {"school": "State University", "degree": "B.S. in CS", "dates": "2016 - 2020"},
    ],
}


def _payload(**overrides: object) -> dict:
    """Return a deep copy of the valid payload with top-level overrides."""
    data = copy.deepcopy(_VALID_PAYLOAD)
    data.update(overrides)
    return data


# ---- Valid data passes ----


class TestValidPayload:
    def test_valid_payload_passes(self) -> None:
        validate_resume_content(_VALID_PAYLOAD)

    def test_valid_payload_require_non_empty(self) -> None:
        validate_resume_content(_VALID_PAYLOAD, require_non_empty=True)


# ---- Skills nested validation ----


class TestSkillsNested:
    def test_missing_category(self) -> None:
        data = _payload(skills=[{"items": "Python"}])
        with pytest.raises(ValueError, match=r"skills\[0\] missing required field: category"):
            validate_resume_content(data)

    def test_missing_items(self) -> None:
        data = _payload(skills=[{"category": "Languages"}])
        with pytest.raises(ValueError, match=r"skills\[0\] missing required field: items"):
            validate_resume_content(data)

    def test_category_wrong_type(self) -> None:
        data = _payload(skills=[{"category": 123, "items": "Python"}])
        with pytest.raises(ValueError, match=r"skills\[0\]\.category must be a str"):
            validate_resume_content(data)

    def test_items_wrong_type(self) -> None:
        data = _payload(skills=[{"category": "Languages", "items": ["Python", "Go"]}])
        with pytest.raises(ValueError, match=r"skills\[0\]\.items must be a str"):
            validate_resume_content(data)

    def test_second_entry_missing_field(self) -> None:
        data = _payload(
            skills=[
                {"category": "Languages", "items": "Python"},
                {"category": "Tools"},
            ]
        )
        with pytest.raises(ValueError, match=r"skills\[1\] missing required field: items"):
            validate_resume_content(data)


# ---- Experience nested validation ----


class TestExperienceNested:
    def test_missing_company(self) -> None:
        data = _payload(
            experience=[{"title": "Eng", "dates": "2020", "bullets": ["x"]}]
        )
        with pytest.raises(ValueError, match=r"experience\[0\] missing required field: company"):
            validate_resume_content(data)

    def test_missing_bullets(self) -> None:
        data = _payload(
            experience=[{"company": "A", "title": "B", "dates": "2020"}]
        )
        with pytest.raises(ValueError, match=r"experience\[0\] missing required field: bullets"):
            validate_resume_content(data)

    def test_bullets_wrong_type(self) -> None:
        data = _payload(
            experience=[
                {"company": "A", "title": "B", "dates": "2020", "bullets": "not a list"}
            ]
        )
        with pytest.raises(ValueError, match=r"experience\[0\]\.bullets must be a list"):
            validate_resume_content(data)

    def test_bullet_element_wrong_type(self) -> None:
        data = _payload(
            experience=[
                {"company": "A", "title": "B", "dates": "2020", "bullets": [42]}
            ]
        )
        with pytest.raises(ValueError, match=r"experience\[0\]\.bullets\[0\] must be a str"):
            validate_resume_content(data)

    def test_second_experience_missing_title(self) -> None:
        data = _payload(
            experience=[
                {"company": "A", "title": "B", "dates": "2020", "bullets": ["x"]},
                {"company": "C", "dates": "2021", "bullets": ["y"]},
            ]
        )
        with pytest.raises(ValueError, match=r"experience\[1\] missing required field: title"):
            validate_resume_content(data)


# ---- Education nested validation ----


class TestEducationNested:
    def test_missing_school(self) -> None:
        data = _payload(education=[{"degree": "B.S.", "dates": "2020"}])
        with pytest.raises(ValueError, match=r"education\[0\] missing required field: school"):
            validate_resume_content(data)

    def test_missing_degree(self) -> None:
        data = _payload(education=[{"school": "Uni", "dates": "2020"}])
        with pytest.raises(ValueError, match=r"education\[0\] missing required field: degree"):
            validate_resume_content(data)

    def test_missing_dates(self) -> None:
        data = _payload(education=[{"school": "Uni", "degree": "B.S."}])
        with pytest.raises(ValueError, match=r"education\[0\] missing required field: dates"):
            validate_resume_content(data)

    def test_school_wrong_type(self) -> None:
        data = _payload(education=[{"school": 123, "degree": "B.S.", "dates": "2020"}])
        with pytest.raises(ValueError, match=r"education\[0\]\.school must be a str"):
            validate_resume_content(data)

    def test_degree_wrong_type(self) -> None:
        data = _payload(education=[{"school": "Uni", "degree": 456, "dates": "2020"}])
        with pytest.raises(ValueError, match=r"education\[0\]\.degree must be a str"):
            validate_resume_content(data)

    def test_dates_wrong_type(self) -> None:
        data = _payload(education=[{"school": "Uni", "degree": "B.S.", "dates": 2020}])
        with pytest.raises(ValueError, match=r"education\[0\]\.dates must be a str"):
            validate_resume_content(data)

    def test_location_wrong_type(self) -> None:
        data = _payload(education=[{"school": "Uni", "degree": "B.S.", "dates": "2020", "location": 123}])
        with pytest.raises(ValueError, match=r"education\[0\]\.location must be a str"):
            validate_resume_content(data)

    def test_location_optional(self) -> None:
        data = _payload(education=[{"school": "Uni", "degree": "B.S.", "dates": "2020"}])
        validate_resume_content(data)  # should not raise
