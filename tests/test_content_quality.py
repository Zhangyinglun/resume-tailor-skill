#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for content-level quality checks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_content_quality import (
    check_bullet_count,
    check_bullet_length,
    check_bullet_starts_with_verb,
    check_duplicate_phrases,
    check_quantification_ratio,
    run_all_checks,
)


def _make_resume(
    experience_bullets: list[list[str]] | None = None,
    project_bullets: list[list[str]] | None = None,
) -> dict:
    """Build a minimal resume dict for testing."""
    experience = []
    for i, bullets in enumerate(experience_bullets or []):
        experience.append({
            "company": f"Company {i}",
            "title": f"Engineer {i}",
            "dates": "2020 - 2024",
            "bullets": bullets,
        })
    projects = []
    for i, bullets in enumerate(project_bullets or []):
        projects.append({
            "name": f"Project {i}",
            "bullets": bullets,
        })
    return {
        "name": "Test User",
        "contact": "test@example.com",
        "summary": "A summary.",
        "skills": [{"category": "Languages", "items": "Python, Go"}],
        "experience": experience,
        "education": [{"school": "MIT", "degree": "BS CS", "dates": "2016-2020"}],
        "projects": projects,
    }


def _write_resume_json(tmpdir: str, resume: dict) -> Path:
    p = Path(tmpdir) / "resume-working.json"
    p.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


class BulletLengthTest(unittest.TestCase):
    def test_all_short_pass(self):
        bullets = ["Built a service in 5 days", "Reduced latency by 30%"]
        result = check_bullet_length(bullets)
        self.assertEqual(result["status"], "PASS")

    def test_long_bullet_warn(self):
        long = " ".join(["word"] * 30)
        bullets = ["Short bullet", long]
        result = check_bullet_length(bullets)
        self.assertEqual(result["status"], "WARN")
        self.assertIn("1 bullet(s)", result["detail"])


class BulletVerbStartTest(unittest.TestCase):
    def test_high_ratio_pass(self):
        bullets = [
            "Built a microservice architecture",
            "Designed the API layer",
            "Reduced deployment time by 50%",
            "Improved test coverage to 90%",
            "Led a team of 5 engineers",
        ]
        result = check_bullet_starts_with_verb(bullets)
        self.assertEqual(result["status"], "PASS")

    def test_low_ratio_warn(self):
        bullets = [
            "The system was redesigned",
            "Responsible for backend services",
            "Working on cloud migration",
            "Helped the team with testing",
            "Built a new pipeline",
        ]
        result = check_bullet_starts_with_verb(bullets)
        self.assertEqual(result["status"], "WARN")


class QuantificationRatioTest(unittest.TestCase):
    def test_high_ratio_pass(self):
        bullets = [
            "Reduced latency by 30%",
            "Grew revenue to $2M",
            "Managed 5 engineers",
            "Improved uptime to 99.9%",
            "Cut costs by 40%",
        ]
        result = check_quantification_ratio(bullets)
        self.assertEqual(result["status"], "PASS")

    def test_low_ratio_warn(self):
        bullets = [
            "Built a new service",
            "Designed the architecture",
            "Led the migration project",
            "Improved developer experience",
            "Streamlined the deployment process",
        ]
        result = check_quantification_ratio(bullets)
        self.assertEqual(result["status"], "WARN")


class DuplicatePhrasesTest(unittest.TestCase):
    def test_no_duplicates_pass(self):
        bullets = [
            "Built a microservice architecture",
            "Designed the API layer",
            "Reduced deployment time significantly",
        ]
        result = check_duplicate_phrases(bullets)
        self.assertEqual(result["status"], "PASS")

    def test_repeated_trigram_warn(self):
        bullets = [
            "improved the performance of the system",
            "improved the performance of the API",
            "improved the performance of the pipeline",
        ]
        result = check_duplicate_phrases(bullets)
        self.assertEqual(result["status"], "WARN")
        self.assertIn("improved the performance", result["detail"])


class BulletCountTest(unittest.TestCase):
    def test_in_range_pass(self):
        bullets = [f"Bullet {i}" for i in range(10)]
        result = check_bullet_count(bullets)
        self.assertEqual(result["status"], "PASS")

    def test_too_few_warn(self):
        bullets = ["Bullet 1", "Bullet 2"]
        result = check_bullet_count(bullets)
        self.assertEqual(result["status"], "WARN")

    def test_too_many_warn(self):
        bullets = [f"Bullet {i}" for i in range(20)]
        result = check_bullet_count(bullets)
        self.assertEqual(result["status"], "WARN")


class RunAllChecksTest(unittest.TestCase):
    def test_integration_all_pass(self):
        resume = _make_resume(
            experience_bullets=[
                [
                    "Built a distributed cache reducing latency by 40%",
                    "Designed RESTful APIs serving 10M requests daily",
                    "Led migration of 3 services to Kubernetes",
                    "Improved CI pipeline speed by 60%",
                    "Reduced infrastructure costs by $200K annually",
                ],
                [
                    "Developed automated testing framework with 95% coverage",
                    "Managed team of 4 engineers across 2 time zones",
                    "Launched real-time analytics dashboard for 500 users",
                    "Streamlined deployment process cutting release time by 50%",
                    "Implemented monitoring alerting system reducing MTTR by 70%",
                ],
            ],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _write_resume_json(tmpdir, resume)
            results = run_all_checks(p)

        self.assertEqual(len(results), 5)
        for r in results:
            self.assertIn("name", r)
            self.assertIn("status", r)
            self.assertIn("detail", r)

    def test_integration_returns_serializable_json(self):
        resume = _make_resume(experience_bullets=[["Built a thing"] * 10])
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _write_resume_json(tmpdir, resume)
            results = run_all_checks(p)
        serialized = json.dumps(results, ensure_ascii=False)
        deserialized = json.loads(serialized)
        self.assertEqual(len(deserialized), 5)


class CliJsonOutputTest(unittest.TestCase):
    def test_json_flag_produces_valid_json(self):
        resume = _make_resume(
            experience_bullets=[
                [
                    "Built a service reducing latency by 30%",
                    "Designed APIs for 5M daily users",
                    "Led team of 8 engineers",
                    "Improved deployment speed by 40%",
                    "Reduced costs by $100K",
                    "Launched monitoring for 99.9% uptime",
                    "Migrated 3 legacy systems to cloud",
                    "Developed CI/CD pipeline with 95% coverage",
                ],
            ],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _write_resume_json(tmpdir, resume)
            result = subprocess.run(
                [sys.executable, "-m", "scripts.check_content_quality", str(p), "--json"],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 5)
            for item in data:
                self.assertIn("name", item)
                self.assertIn("status", item)
                self.assertIn("detail", item)


if __name__ == "__main__":
    unittest.main()
