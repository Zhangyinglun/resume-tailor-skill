from __future__ import annotations

import unittest
from typing import Any

from scripts.check_content_quality import run_all_checks


def resume_with(experience: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": "Backend engineer.",
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


if __name__ == "__main__":
    unittest.main()
