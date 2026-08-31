from __future__ import annotations

import unittest

from scripts.check_pdf_geometry import detect_sparse_bullet_endings


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


if __name__ == "__main__":
    unittest.main()
