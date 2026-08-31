from __future__ import annotations

import unittest
from typing import Any

from scripts.resume_shared import (
    has_quantified_result,
    iter_resume_text_fields,
    normalize_skill_items,
    score_bullet,
    term_matches,
    validate_resume_content,
)


def sample_resume() -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": "Backend engineer building distributed systems.",
        "skills": [{"category": "Languages", "items": "Python, Go, C++"}],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "dates": "2020 - Present",
                "bullets": ["Built distributed APIs using Python."],
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "B.S. Computer Science",
                "dates": "2016 - 2020",
            }
        ],
    }


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

    def test_validator_skills_rejects_empty_array(self) -> None:
        resume = sample_resume()
        resume["skills"] = [{"category": "Languages", "items": []}]
        with self.assertRaisesRegex(ValueError, "empty array"):
            validate_resume_content(resume)

    def test_validator_skills_rejects_invalid_elements(self) -> None:
        resume = sample_resume()
        resume["skills"] = [{"category": "Languages", "items": ["Python", ""]}]
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            validate_resume_content(resume)

        resume["skills"] = [{"category": "Languages", "items": ["Python", 123]}]
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            validate_resume_content(resume)

    def test_validator_skills_rejects_non_string_non_list(self) -> None:
        resume = sample_resume()
        resume["skills"] = [{"category": "Languages", "items": 123}]
        with self.assertRaisesRegex(ValueError, "str or list"):
            validate_resume_content(resume)

    def test_normalize_skill_items_accepts_list_and_legacy_string(self) -> None:
        self.assertEqual(
            normalize_skill_items(["Azure OpenAI", "MCP", "RAG"]),
            ["Azure OpenAI", "MCP", "RAG"],
        )
        self.assertEqual(
            normalize_skill_items("Azure OpenAI, MCP, RAG"),
            ["Azure OpenAI", "MCP", "RAG"],
        )

    def test_iter_resume_text_fields_emits_item_level_skill_paths(self) -> None:
        resume = sample_resume()
        resume["skills"] = [
            {
                "category": "AI Platforms & Tooling",
                "items": ["Azure OpenAI", "MCP", "RAG"],
            }
        ]
        validate_resume_content(resume, require_non_empty=True)

        fields = {path: text for path, text, _, _ in iter_resume_text_fields(resume)}

        self.assertEqual(fields["skills[0].category"], "AI Platforms & Tooling")
        self.assertEqual(fields["skills[0].items[0]"], "Azure OpenAI")
        self.assertEqual(fields["skills[0].items[1]"], "MCP")
        self.assertEqual(fields["skills[0].items[2]"], "RAG")
        self.assertNotIn("skills[0].items", fields)

    def test_iter_resume_text_fields_preserves_legacy_skill_path(self) -> None:
        resume = sample_resume()
        resume["skills"] = [{"category": "Languages", "items": "Python, Go"}]

        fields = {path: text for path, text, _, _ in iter_resume_text_fields(resume)}

        self.assertEqual(fields["skills[0].items"], "Python, Go")


if __name__ == "__main__":
    unittest.main()
