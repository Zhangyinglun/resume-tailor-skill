#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for bullet relevance scoring."""

from __future__ import annotations

import unittest

from scripts.resume_shared import _extract_terms, score_all_bullets, score_bullet


class TestExtractTerms(unittest.TestCase):
    """Tests for _extract_terms helper."""

    def test_extract_terms_from_strings(self) -> None:
        result = _extract_terms(["Python", "AWS"])
        self.assertEqual(result, ["python", "aws"])

    def test_extract_terms_from_dicts(self) -> None:
        result = _extract_terms([{"term": "Python"}, {"term": "AWS"}])
        self.assertEqual(result, ["python", "aws"])

    def test_extract_terms_mixed(self) -> None:
        result = _extract_terms(["Python", {"term": "AWS"}, 42, {"no_term": "x"}])
        self.assertEqual(result, ["python", "aws"])


class TestScoreBullet(unittest.TestCase):
    """Tests for score_bullet function."""

    def test_score_bullet_p1_hit(self) -> None:
        result = score_bullet(
            "Built a Python microservice for data processing",
            p1_terms=["python"],
            p2_terms=[],
            p3_terms=[],
        )
        self.assertGreaterEqual(result["score"], 3)
        self.assertIn("python", result["p1_hits"])

    def test_score_bullet_no_hits(self) -> None:
        result = score_bullet(
            "Attended weekly team meetings",
            p1_terms=["python", "aws"],
            p2_terms=["microservices"],
            p3_terms=["agile"],
        )
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["p1_hits"], [])
        self.assertEqual(result["p2_hits"], [])
        self.assertEqual(result["p3_hits"], [])

    def test_score_bullet_quantification_bonus(self) -> None:
        result = score_bullet(
            "Reduced latency by 40% across all services",
            p1_terms=[],
            p2_terms=[],
            p3_terms=[],
        )
        self.assertTrue(result["has_quantification"])

    def test_score_bullet_four_elements(self) -> None:
        result = score_bullet(
            "Designed and deployed Python microservice reducing API latency by 40% across 5 regions",
            p1_terms=["python"],
            p2_terms=[],
            p3_terms=[],
        )
        self.assertTrue(result["has_four_elements"])

    def test_score_bullet_multiple_tiers(self) -> None:
        result = score_bullet(
            "Used Python to build microservices on the platform",
            p1_terms=["python"],
            p2_terms=["microservices"],
            p3_terms=[],
        )
        # 3 (P1) + 2 (P2) = 5, no number so no quantification/four-element bonus
        self.assertEqual(result["score"], 5)


class TestScoreAllBullets(unittest.TestCase):
    """Tests for score_all_bullets function."""

    def test_score_all_bullets_ordering(self) -> None:
        resume = {
            "experience": [
                {
                    "company": "Acme",
                    "title": "Engineer",
                    "dates": "2020-2024",
                    "bullets": [
                        "Attended meetings regularly",
                        "Built Python microservices on AWS serving 1M requests daily",
                    ],
                }
            ]
        }
        jd = {"keywords": {"P1": ["python", "aws"], "P2": [], "P3": []}}
        scored = score_all_bullets(resume, jd)
        self.assertEqual(len(scored), 2)
        self.assertGreaterEqual(scored[0]["score"], scored[1]["score"])

    def test_score_all_bullets_paths(self) -> None:
        resume = {
            "experience": [
                {
                    "company": "A",
                    "title": "E",
                    "dates": "2020",
                    "bullets": ["bullet zero", "bullet one"],
                },
                {
                    "company": "B",
                    "title": "E",
                    "dates": "2021",
                    "bullets": ["bullet two"],
                },
            ]
        }
        jd = {"keywords": {"P1": [], "P2": [], "P3": []}}
        scored = score_all_bullets(resume, jd)
        paths = {entry["path"] for entry in scored}
        self.assertIn("experience[0].bullets[0]", paths)
        self.assertIn("experience[0].bullets[1]", paths)
        self.assertIn("experience[1].bullets[0]", paths)

    def test_score_all_bullets_empty(self) -> None:
        scored = score_all_bullets({}, {"keywords": {"P1": ["python"]}})
        self.assertEqual(scored, [])


if __name__ == "__main__":
    unittest.main()
