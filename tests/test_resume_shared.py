from __future__ import annotations

import unittest

from scripts.resume_shared import (
    has_quantified_result,
    score_bullet,
    term_matches,
    validate_resume_content,
)


class ResumeSharedTests(unittest.TestCase):
    def test_short_keywords_require_boundaries(self) -> None:
        self.assertFalse(term_matches("Maintained negotiation services", "AI"))
        self.assertFalse(term_matches("Negotiated vendor contracts", "Go"))
        self.assertTrue(term_matches("Built services in Go", "Go"))
        self.assertTrue(term_matches("Developed with C++ and C#", "C++"))

    def test_quantification_ignores_bare_versions(self) -> None:
        self.assertFalse(has_quantified_result("Migrated services to Python 3"))
        self.assertTrue(has_quantified_result("Reduced latency by 40%"))
        self.assertTrue(has_quantified_result("Cut response time to 25 ms"))

    def test_complete_bullet_structure_does_not_require_a_number(self) -> None:
        complete = score_bullet(
            "Built Kubernetes services using Terraform, improving deployment reliability.",
            ["Kubernetes"],
            [],
            [],
        )
        incomplete = score_bullet(
            "Kubernetes services ran on Python 3 for production workloads.",
            ["Kubernetes"],
            [],
            [],
        )
        self.assertTrue(complete["has_four_elements"])
        self.assertFalse(complete["has_quantification"])
        self.assertFalse(incomplete["has_four_elements"])

    def test_validator_rejects_non_string_fields(self) -> None:
        payload = {
            "name": 123,
            "contact": "a@example.com",
            "summary": "Engineer",
            "skills": [{"category": "Languages", "items": "Python"}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built services."],
                }
            ],
            "education": [
                {"school": "Example", "degree": "B.S.", "dates": "2020"}
            ],
        }
        with self.assertRaisesRegex(ValueError, "name"):
            validate_resume_content(payload)


if __name__ == "__main__":
    unittest.main()
