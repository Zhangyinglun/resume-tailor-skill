from __future__ import annotations

import unittest

from scripts.generate_quality_report import build_keyword_coverage, generate_report


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

    def test_report_includes_factual_audit_coverage_and_findings(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com | +1 206-555-0100",
            "summary": "Engineer",
            "skills": [{"category": "Languages", "items": "Python"}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built services using Python, improving reliability."],
                }
            ],
            "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
        }
        factual_report = {
            "verdict": "FAIL",
            "coverage": {"covered_fields": 9, "total_fields": 10, "coverage_percent": 90.0},
            "findings": [
                {
                    "code": "UNSUPPORTED_METRIC",
                    "severity": "ERROR",
                    "path": "experience[0].bullets[0]",
                    "message": "Metric is unsupported.",
                }
            ],
        }

        report = generate_report(resume, None, factual_report=factual_report)

        self.assertIn("Factual Integrity", report)
        self.assertIn("90.0%", report)
        self.assertIn("UNSUPPORTED_METRIC", report)


if __name__ == "__main__":
    unittest.main()
