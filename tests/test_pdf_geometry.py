from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from scripts.check_pdf_geometry import (
    _section_geometry,
    build_content_fit_feedback,
    detect_sparse_bullet_endings,
    estimate_page_margins_mm,
    main,
    points_to_mm,
)


class PdfGeometryTests(unittest.TestCase):
    def test_detects_sparse_trailing_line_from_rendered_coordinates(self) -> None:
        lines = [
            {
                "text": "• Built a distributed cache using Redis to improve",
                "x0": 42.0,
                "x1": 510.0,
                "top": 100.0,
                "bottom": 109.0,
                "words": [
                    "•",
                    "Built",
                    "a",
                    "distributed",
                    "cache",
                    "using",
                    "Redis",
                    "to",
                    "improve",
                ],
            },
            {
                "text": "reliability.",
                "x0": 50.0,
                "x1": 105.0,
                "top": 109.0,
                "bottom": 118.0,
                "words": ["reliability."],
            },
        ]

        findings = detect_sparse_bullet_endings(lines, page_width=595.0)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["word_count"], 1)
        self.assertIn("reliability", findings[0]["text"])

    def test_accepts_well_filled_trailing_line(self) -> None:
        lines = [
            {
                "text": "• Built a distributed cache using Redis to improve",
                "x0": 42.0,
                "x1": 510.0,
                "top": 100.0,
                "bottom": 109.0,
                "words": [
                    "•",
                    "Built",
                    "a",
                    "distributed",
                    "cache",
                    "using",
                    "Redis",
                    "to",
                    "improve",
                ],
            },
            {
                "text": "reliability across all production services and regions.",
                "x0": 50.0,
                "x1": 430.0,
                "top": 109.0,
                "bottom": 118.0,
                "words": [
                    "reliability",
                    "across",
                    "all",
                    "production",
                    "services",
                    "and",
                    "regions",
                ],
            },
        ]

        self.assertEqual(detect_sparse_bullet_endings(lines, page_width=595.0), [])

    def test_section_geometry_partitions_lines_and_calculates_counts_and_heights(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com | +1 206-555-0100",
            "summary": "Backend engineer.",
            "skills": [{"category": "Languages", "items": ["Python", "Go"]}],
            "experience": [
                {
                    "company": "Example Corp",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built a Python service."],
                }
            ],
            "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
        }
        lines = [
            {"text": "SUMMARY", "top": 20.0, "bottom": 30.0, "x0": 50.0, "x1": 120.0, "words": ["SUMMARY"]},
            {"text": "Backend engineer.", "top": 32.0, "bottom": 42.0, "x0": 50.0, "x1": 180.0, "words": ["Backend", "engineer."]},
            {"text": "PROFESSIONAL EXPERIENCE", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 240.0, "words": ["PROFESSIONAL", "EXPERIENCE"]},
            {"text": "Example Corp", "top": 62.0, "bottom": 72.0, "x0": 50.0, "x1": 130.0, "words": ["Example", "Corp"]},
            {"text": "• Built a Python service.", "top": 74.0, "bottom": 84.0, "x0": 55.0, "x1": 220.0, "words": ["•", "Built", "a", "Python", "service."]},
            {"text": "TECHNICAL SKILLS", "top": 90.0, "bottom": 100.0, "x0": 50.0, "x1": 180.0, "words": ["TECHNICAL", "SKILLS"]},
            {"text": "Languages: Python, Go", "top": 102.0, "bottom": 112.0, "x0": 50.0, "x1": 210.0, "words": ["Languages:", "Python,", "Go"]},
        ]
        geometry = _section_geometry(lines, resume)
        self.assertEqual(geometry["summary"]["line_count"], 1)
        self.assertEqual(geometry["experience[0]"]["line_count"], 2)
        self.assertEqual(geometry["skills"]["line_count"], 1)
        self.assertAlmostEqual(geometry["summary"]["height_mm"], points_to_mm(10.0), places=1)
        self.assertAlmostEqual(geometry["experience[0]"]["height_mm"], points_to_mm(22.0), places=1)

    def test_section_geometry_disambiguates_duplicate_companies_using_dates(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "experience": [
                {
                    "company": "Acme Corp",
                    "title": "Senior Engineer",
                    "dates": "2022 - Present",
                    "bullets": ["Led distributed team."],
                },
                {
                    "company": "Acme Corp",
                    "title": "Software Engineer",
                    "dates": "2020 - 2022",
                    "bullets": ["Built Python microservices."],
                },
            ],
        }
        lines = [
            {"text": "EXPERIENCE", "top": 40.0, "bottom": 50.0, "x0": 50.0, "x1": 150.0, "words": ["EXPERIENCE"]},
            {"text": "Acme Corp | Senior Engineer 2022 - Present", "top": 55.0, "bottom": 65.0, "x0": 50.0, "x1": 350.0, "words": ["Acme", "Corp"]},
            {"text": "• Led distributed team.", "top": 67.0, "bottom": 77.0, "x0": 55.0, "x1": 250.0, "words": ["•", "Led"]},
            {"text": "Acme Corp | Software Engineer 2020 - 2022", "top": 85.0, "bottom": 95.0, "x0": 50.0, "x1": 350.0, "words": ["Acme", "Corp"]},
            {"text": "• Built Python microservices.", "top": 97.0, "bottom": 107.0, "x0": 55.0, "x1": 270.0, "words": ["•", "Built"]},
        ]
        geometry = _section_geometry(lines, resume)
        self.assertEqual(geometry["experience[0]"]["line_count"], 2)
        self.assertEqual(geometry["experience[1]"]["line_count"], 2)

    def test_section_geometry_falls_back_to_aggregate_when_unmatched(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "experience": [
                {
                    "company": "Unknown Corp",
                    "title": "Engineer",
                    "dates": "2020 - 2022",
                    "bullets": ["Built services."],
                }
            ],
        }
        lines = [
            {"text": "WORK EXPERIENCE", "top": 40.0, "bottom": 50.0, "x0": 50.0, "x1": 180.0, "words": ["WORK", "EXPERIENCE"]},
            {"text": "Mismatched Header Line", "top": 55.0, "bottom": 65.0, "x0": 50.0, "x1": 250.0, "words": ["Mismatched"]},
            {"text": "• Built services.", "top": 67.0, "bottom": 77.0, "x0": 55.0, "x1": 200.0, "words": ["•", "Built"]},
        ]
        geometry = _section_geometry(lines, resume)
        self.assertIn("experience", geometry)
        self.assertNotIn("experience[0]", geometry)
        self.assertEqual(geometry["experience"]["line_count"], 2)

    def _make_mock_page(
        self,
        *,
        words: list[dict[str, Any]],
        width: float = 595.28,
        height: float = 841.89,
    ) -> mock.MagicMock:
        page = mock.MagicMock()
        page.width = width
        page.height = height
        page.extract_words.return_value = words
        return page

    def test_estimate_page_margins_mm(self) -> None:
        words = [
            {"text": "TopWord", "top": 72.0, "bottom": 82.0, "x0": 72.0, "x1": 150.0},
            {"text": "BottomWord", "top": 700.0, "bottom": 710.0, "x0": 100.0, "x1": 500.0},
        ]
        page = self._make_mock_page(words=words, width=600.0, height=800.0)
        margins = estimate_page_margins_mm(page)
        self.assertIsNotNone(margins)
        assert margins is not None
        self.assertAlmostEqual(margins["top"], points_to_mm(72.0), places=1)
        self.assertAlmostEqual(margins["bottom"], points_to_mm(800.0 - 710.0), places=1)
        self.assertAlmostEqual(margins["left"], points_to_mm(72.0), places=1)
        self.assertAlmostEqual(margins["right"], points_to_mm(600.0 - 500.0), places=1)

    def test_build_content_fit_feedback_overflow_on_multi_page(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "summary": "Experienced engineer.",
            "skills": [{"category": "L", "items": ["Go"]}],
            "experience": [{"company": "C", "title": "T", "dates": "D", "bullets": ["B"]}],
            "education": [{"school": "S", "degree": "D", "dates": "2020"}],
        }
        p1_words = [
            {"text": "Alex", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 100.0},
            {"text": "TECHNICAL", "top": 70.0, "bottom": 80.0, "x0": 50.0, "x1": 120.0},
            {"text": "SKILLS", "top": 70.0, "bottom": 80.0, "x0": 125.0, "x1": 160.0},
            {"text": "L: Go", "top": 85.0, "bottom": 95.0, "x0": 50.0, "x1": 100.0},
            {"text": "L2", "top": 98.0, "bottom": 108.0, "x0": 50.0, "x1": 100.0},
        ]
        p2_words = [
            {"text": "Overflow", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 100.0}
        ]
        page1 = self._make_mock_page(words=p1_words)
        page2 = self._make_mock_page(words=p2_words)

        mock_pdf = mock.MagicMock()
        mock_pdf.pages = [page1, page2]
        mock_pdf.__enter__.return_value = mock_pdf

        with mock.patch("scripts.check_pdf_geometry.pdfplumber.open", return_value=mock_pdf):
            feedback = build_content_fit_feedback(
                Path("/fake/resume.pdf"),
                resume,
                plan_revision=1,
            )

        self.assertEqual(feedback["schema_version"], 1)
        self.assertEqual(feedback["plan_revision"], 1)
        self.assertEqual(feedback["verdict"], "overflow")
        self.assertEqual(feedback["page_count"], 2)

    def test_build_content_fit_feedback_underfill_when_bottom_whitespace_exceeds_budget(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "summary": "Experienced engineer.",
            "skills": [
                {"category": "L", "items": ["Python", "Go"]},
                {"category": "D", "items": ["PostgreSQL"]},
            ],
            "experience": [{"company": "C", "title": "T", "dates": "D", "bullets": ["B"]}],
            "education": [{"school": "S", "degree": "D", "dates": "2020"}],
        }
        # Rendered text only reaches y = 500 on an 841.89 pt page -> bottom margin ~ 120mm > 8mm
        words = [
            {"text": "Alex", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 100.0},
            {"text": "TECHNICAL", "top": 70.0, "bottom": 80.0, "x0": 50.0, "x1": 120.0},
            {"text": "SKILLS", "top": 70.0, "bottom": 80.0, "x0": 125.0, "x1": 160.0},
            {"text": "L: Python, Go", "top": 85.0, "bottom": 95.0, "x0": 50.0, "x1": 150.0},
            {"text": "D: PostgreSQL", "top": 98.0, "bottom": 108.0, "x0": 50.0, "x1": 150.0},
        ]
        page = self._make_mock_page(words=words)
        mock_pdf = mock.MagicMock()
        mock_pdf.pages = [page]
        mock_pdf.__enter__.return_value = mock_pdf

        with mock.patch("scripts.check_pdf_geometry.pdfplumber.open", return_value=mock_pdf):
            feedback = build_content_fit_feedback(
                Path("/fake/resume.pdf"),
                resume,
                plan_revision=2,
                preferred_max_bottom_mm=8.0,
            )

        self.assertEqual(feedback["verdict"], "underfill")
        self.assertEqual(feedback["plan_revision"], 2)
        self.assertGreater(feedback["bottom_whitespace_mm"], 8.0)

    def test_build_content_fit_feedback_revision_required_for_skills_budget(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "summary": "Experienced engineer.",
            "skills": [
                {"category": "1", "items": ["A"]},
                {"category": "2", "items": ["B"]},
                {"category": "3", "items": ["C"]},
                {"category": "4", "items": ["D"]},
                {"category": "5", "items": ["E"]},
            ],
            "experience": [{"company": "C", "title": "T", "dates": "D", "bullets": ["B"]}],
            "education": [{"school": "S", "degree": "D", "dates": "2020"}],
        }
        # 5 skill lines, bottom whitespace within budget
        words = [
            {"text": "Alex", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 100.0},
            {"text": "TECHNICAL", "top": 70.0, "bottom": 80.0, "x0": 50.0, "x1": 120.0},
            {"text": "SKILLS", "top": 70.0, "bottom": 80.0, "x0": 125.0, "x1": 160.0},
            {"text": "1: A", "top": 85.0, "bottom": 95.0, "x0": 50.0, "x1": 100.0},
            {"text": "2: B", "top": 98.0, "bottom": 108.0, "x0": 50.0, "x1": 100.0},
            {"text": "3: C", "top": 110.0, "bottom": 120.0, "x0": 50.0, "x1": 100.0},
            {"text": "4: D", "top": 122.0, "bottom": 132.0, "x0": 50.0, "x1": 100.0},
            {"text": "5: E", "top": 134.0, "bottom": 144.0, "x0": 50.0, "x1": 100.0},
            # Text at bottom of page so bottom margin is ~6mm (within 8mm preferred max)
            {"text": "Footer line", "top": 820.0, "bottom": 825.0, "x0": 50.0, "x1": 100.0},
        ]
        page = self._make_mock_page(words=words)
        mock_pdf = mock.MagicMock()
        mock_pdf.pages = [page]
        mock_pdf.__enter__.return_value = mock_pdf

        with mock.patch("scripts.check_pdf_geometry.pdfplumber.open", return_value=mock_pdf):
            feedback = build_content_fit_feedback(
                Path("/fake/resume.pdf"),
                resume,
                plan_revision=1,
            )

        self.assertEqual(feedback["verdict"], "revision_required")
        self.assertIn("skills_rendered_line_budget", feedback["issues"])

    def test_build_content_fit_feedback_fit_verdict_and_sparse_bullets(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "summary": "Experienced engineer.",
            "skills": [
                {"category": "Languages", "items": ["Python", "Go"]},
                {"category": "Cloud", "items": ["AWS", "GCP"]},
            ],
            "experience": [{"company": "C", "title": "T", "dates": "D", "bullets": ["B"]}],
            "education": [{"school": "S", "degree": "D", "dates": "2020"}],
        }
        # 2 skill lines, then experience section with sparse ending, bottom whitespace ~ 6mm
        words = [
            {"text": "Alex", "top": 50.0, "bottom": 60.0, "x0": 50.0, "x1": 100.0},
            {"text": "TECHNICAL", "top": 70.0, "bottom": 80.0, "x0": 50.0, "x1": 120.0},
            {"text": "SKILLS", "top": 70.0, "bottom": 80.0, "x0": 125.0, "x1": 160.0},
            {"text": "Languages: Python, Go", "top": 85.0, "bottom": 95.0, "x0": 50.0, "x1": 200.0},
            {"text": "Cloud: AWS, GCP", "top": 98.0, "bottom": 108.0, "x0": 50.0, "x1": 200.0},
            # Experience header and entry
            {"text": "EXPERIENCE", "top": 110.0, "bottom": 120.0, "x0": 50.0, "x1": 150.0},
            {"text": "C | T D", "top": 122.0, "bottom": 132.0, "x0": 50.0, "x1": 150.0},
            # Bullet with sparse ending
            {"text": "•", "top": 134.0, "bottom": 144.0, "x0": 50.0, "x1": 55.0},
            {"text": "Built", "top": 134.0, "bottom": 144.0, "x0": 60.0, "x1": 100.0},
            {"text": "distributed", "top": 134.0, "bottom": 144.0, "x0": 105.0, "x1": 180.0},
            {"text": "services", "top": 134.0, "bottom": 144.0, "x0": 185.0, "x1": 250.0},
            {"text": "across", "top": 134.0, "bottom": 144.0, "x0": 255.0, "x1": 310.0},
            {"text": "regions", "top": 134.0, "bottom": 144.0, "x0": 315.0, "x1": 380.0},
            {"text": "safely.", "top": 146.0, "bottom": 156.0, "x0": 55.0, "x1": 100.0},
            # Text near bottom
            {"text": "Bottom", "top": 820.0, "bottom": 825.0, "x0": 50.0, "x1": 100.0},
        ]
        page = self._make_mock_page(words=words)
        mock_pdf = mock.MagicMock()
        mock_pdf.pages = [page]
        mock_pdf.__enter__.return_value = mock_pdf

        with mock.patch("scripts.check_pdf_geometry.pdfplumber.open", return_value=mock_pdf):
            feedback = build_content_fit_feedback(
                Path("/fake/resume.pdf"),
                resume,
                plan_revision=1,
            )

        self.assertEqual(feedback["verdict"], "fit")
        self.assertEqual(feedback["issues"], [])
        self.assertEqual(len(feedback["sparse_trailing_bullets"]), 1)
        self.assertIn("safely", feedback["sparse_trailing_bullets"][0]["text"])

    def test_cli_feedback_output_and_plan_revision(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "summary": "Experienced engineer.",
            "skills": [{"category": "L", "items": ["Python", "Go"]}],
            "experience": [{"company": "C", "title": "T", "dates": "D", "bullets": ["B"]}],
            "education": [{"school": "S", "degree": "D", "dates": "2020"}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / "resume.pdf"
            pdf_path.write_bytes(b"%PDF-mock")
            resume_path = temp_path / "resume.json"
            resume_path.write_text(json.dumps(resume), encoding="utf-8")
            feedback_path = temp_path / "feedback.json"

            mock_feedback = {
                "schema_version": 1,
                "plan_revision": 3,
                "verdict": "fit",
                "page_count": 1,
                "bottom_whitespace_mm": 5.5,
                "section_geometry": {"skills": {"line_count": 2, "height_mm": 10.0}},
                "sparse_trailing_bullets": [],
                "issues": [],
            }

            with mock.patch(
                "scripts.check_pdf_geometry.build_content_fit_feedback",
                return_value=mock_feedback,
            ):
                argv = [
                    "check_pdf_geometry.py",
                    str(pdf_path),
                    "--resume",
                    str(resume_path),
                    "--plan-revision",
                    "3",
                    "--feedback-output",
                    str(feedback_path),
                    "--json",
                ]
                stdout = io.StringIO()
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
                    result = main()

                self.assertEqual(result, 0)
                self.assertTrue(feedback_path.exists())
                saved = json.loads(feedback_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["plan_revision"], 3)
                self.assertEqual(saved["verdict"], "fit")
                self.assertIn('"verdict": "fit"', stdout.getvalue())


    def test_section_geometry_other_sections(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "projects": [{"name": "Project Alpha", "bullets": ["Built a thing."]}],
            "awards": [{"name": "Best Engineer", "organization": "Org"}],
            "certifications": [{"name": "AWS Pro", "issuer": "Amazon"}],
            "education": [{"school": "University", "degree": "B.S."}],
        }
        lines = [
            {"text": "PROJECTS", "top": 20.0, "bottom": 30.0, "x0": 50.0, "x1": 120.0, "words": ["PROJECTS"]},
            {"text": "Project Alpha | Tech", "top": 35.0, "bottom": 45.0, "x0": 50.0, "x1": 200.0, "words": ["Project"]},
            {"text": "• Built a thing.", "top": 48.0, "bottom": 58.0, "x0": 55.0, "x1": 180.0, "words": ["•", "Built"]},
            {"text": "AWARDS", "top": 70.0, "bottom": 80.0, "x0": 50.0, "x1": 120.0, "words": ["AWARDS"]},
            {"text": "Best Engineer - Org", "top": 85.0, "bottom": 95.0, "x0": 50.0, "x1": 200.0, "words": ["Best"]},
            {"text": "CERTIFICATIONS", "top": 110.0, "bottom": 120.0, "x0": 50.0, "x1": 150.0, "words": ["CERTIFICATIONS"]},
            {"text": "AWS Pro - Amazon", "top": 125.0, "bottom": 135.0, "x0": 50.0, "x1": 200.0, "words": ["AWS"]},
            {"text": "EDUCATION", "top": 150.0, "bottom": 160.0, "x0": 50.0, "x1": 130.0, "words": ["EDUCATION"]},
            {"text": "University 2020", "top": 165.0, "bottom": 175.0, "x0": 50.0, "x1": 200.0, "words": ["University"]},
        ]
        geometry = _section_geometry(lines, resume)
        self.assertEqual(geometry["projects"]["line_count"], 2)
        self.assertEqual(geometry["awards"]["line_count"], 1)
        self.assertEqual(geometry["certifications"]["line_count"], 1)
        self.assertEqual(geometry["education"]["line_count"], 1)

    def test_cli_default_sparse_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / "resume.pdf"
            pdf_path.write_bytes(b"%PDF-mock")

            mock_report = {
                "verdict": "PASS",
                "sparse_trailing_line_count": 0,
                "pages": [{"page": 1, "sparse_trailing_lines": []}],
            }
            with mock.patch("scripts.check_pdf_geometry.check_pdf_geometry", return_value=mock_report):
                argv = ["check_pdf_geometry.py", str(pdf_path), "--json"]
                stdout = io.StringIO()
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
                    result = main()

                self.assertEqual(result, 0)
                self.assertIn('"verdict": "PASS"', stdout.getvalue())

    def test_cli_error_handling_and_non_fit_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / "resume.pdf"
            pdf_path.write_bytes(b"%PDF-mock")
            resume_path = temp_path / "resume.json"
            resume_path.write_text("invalid json", encoding="utf-8")

            # 1. Invalid resume JSON gives error exit code 1
            argv = ["check_pdf_geometry.py", str(pdf_path), "--resume", str(resume_path)]
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                result = main()
            self.assertEqual(result, 1)

            # 2. Non-existent PDF gives exit code 1
            argv = ["check_pdf_geometry.py", str(temp_path / "non_existent.pdf")]
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                result = main()
            self.assertEqual(result, 1)

            # 3. Non-fit verdict gives exit code 2
            resume_path.write_text(json.dumps({"name": "A"}), encoding="utf-8")
            mock_overflow = {
                "schema_version": 1,
                "plan_revision": 1,
                "verdict": "overflow",
                "page_count": 2,
                "bottom_whitespace_mm": None,
                "section_geometry": {},
                "sparse_trailing_bullets": [],
                "issues": [],
            }
            with mock.patch(
                "scripts.check_pdf_geometry.build_content_fit_feedback",
                return_value=mock_overflow,
            ):
                argv = ["check_pdf_geometry.py", str(pdf_path), "--resume", str(resume_path)]
                stdout = io.StringIO()
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
                    result = main()
                self.assertEqual(result, 2)
                self.assertIn("overflow", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
