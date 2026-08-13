from __future__ import annotations

import unittest

from scripts.generate_quality_report import build_keyword_coverage


class QualityReportTests(unittest.TestCase):
    def test_coverage_uses_boundaries_and_all_evidence_sections(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com | +1 206-555-0100",
            "summary": "Maintained distributed services.",
            "skills": [{"category": "Languages", "items": "Python"}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Software Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built reliable APIs using Python."],
                }
            ],
            "projects": [
                {
                    "name": "Runtime",
                    "tech": "Go, C++",
                    "dates": "2024",
                    "bullets": ["Built a local runtime in Go."],
                }
            ],
            "education": [
                {
                    "school": "Example University",
                    "degree": "B.S. Computer Science",
                    "dates": "2020",
                }
            ],
        }
        jd = {"keywords": {"P1": ["AI", "Go", "C++"], "P2": [], "P3": []}}
        coverage = build_keyword_coverage(resume, jd)["P1"]
        by_keyword = {entry["keyword"]: entry for entry in coverage}
        self.assertFalse(by_keyword["ai"]["covered"])
        self.assertTrue(by_keyword["go"]["covered"])
        self.assertTrue(by_keyword["c++"]["covered"])
        self.assertIn("projects[0].tech", by_keyword["c++"]["location"])


if __name__ == "__main__":
    unittest.main()
