from __future__ import annotations

import unittest
from typing import Any

from scripts.check_content_quality import (
    check_resume_language_patterns,
    run_all_checks,
)


def resume_with(
    experience: list[dict[str, Any]],
    summary: str = "Backend engineer.",
) -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": summary,
        "skills": [{"category": "Languages", "items": "Python"}],
        "experience": experience,
        "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
    }


class ContentQualityTests(unittest.TestCase):
    def test_qualitative_results_do_not_trigger_quantification_pressure(self) -> None:
        resume = resume_with(
            [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": [
                        "Built a deployment guard using Python, preventing invalid releases.",
                        "Designed service recovery workflows to improve operational resilience.",
                        "Automated schema validation with Python, reducing integration risk.",
                    ],
                }
            ]
        )

        checks = run_all_checks(resume)
        names = {check["name"] for check in checks}

        self.assertNotIn("quantification_ratio", names)
        self.assertNotIn("bullet_line_fill", names)
        self.assertTrue(all(check["status"] == "PASS" for check in checks))

    def test_bullet_density_adapts_to_number_of_experience_entries(self) -> None:
        entries = [
            {
                "company": f"Company {index}",
                "title": "Engineer",
                "dates": "2020 - Present",
                "bullets": [
                    "Built reliable services using Python, improving operational resilience.",
                    "Automated release checks with Python, preventing invalid deployments.",
                ],
            }
            for index in range(3)
        ]

        check = next(
            item for item in run_all_checks(resume_with(entries))
            if item["name"] == "bullet_density"
        )

        self.assertEqual(check["status"], "PASS")
        self.assertIn("3 experience entries", check["detail"])

    def test_language_pattern_cluster_warns_without_claiming_ai_authorship(self) -> None:
        resume = resume_with(
            [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": [
                        "Successfully leveraged a cutting-edge platform, fostering seamless collaboration.",
                        "Not only improved reliability, but also transformed the engineering landscape.",
                    ],
                }
            ]
        )

        check = next(
            item for item in run_all_checks(resume)
            if item["name"] == "language_pattern_cluster"
        )

        self.assertEqual(check["status"], "WARN")
        self.assertIn("promotional_language", check["detail"])
        self.assertIn("negative_parallelism", check["detail"])
        self.assertNotIn("probability", check["detail"].casefold())
        self.assertNotIn("detector", check["detail"].casefold())
        self.assertNotIn("ai-generated", check["detail"].casefold())

    def test_language_patterns_pass_for_standard_technical_and_list_phrasing(self) -> None:
        resume = resume_with(
            [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": [
                        "Led API design, SDK documentation, and launch reviews.",
                        "Built Go, C#, and Python services.",
                        "Architected a robust microservices infrastructure.",
                    ],
                }
            ]
        )

        check = next(
            item for item in run_all_checks(resume)
            if item["name"] == "language_pattern_cluster"
        )

        self.assertEqual(check["status"], "PASS")

    def test_single_pattern_in_single_bullet_does_not_warn(self) -> None:
        result = check_resume_language_patterns(
            ["Successfully deployed the service to production."]
        )
        self.assertEqual(result["status"], "PASS")

    def test_same_pattern_family_across_multiple_bullets_warns(self) -> None:
        result = check_resume_language_patterns(
            [
                "Successfully deployed the service to production.",
                "Strategically aligned backend architecture with product goals.",
            ]
        )
        self.assertEqual(result["status"], "WARN")
        self.assertIn("empty_qualifier", result["detail"])


if __name__ == "__main__":
    unittest.main()

