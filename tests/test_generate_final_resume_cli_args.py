import sys
import unittest
from unittest.mock import patch

from scripts.generate_final_resume import parse_args


class GenerateFinalResumeCliArgsTest(unittest.TestCase):
    def test_parse_args_supports_layout_parameters(self):
        argv = [
            "generate_final_resume.py",
            "--input-json",
            "cache/resume-working.json",
            "--output-file",
            "resume.pdf",
            "--font-size-scale",
            "0.95",
            "--line-height-scale",
            "0.92",
            "--section-spacing-scale",
            "0.85",
            "--item-spacing-scale",
            "0.8",
            "--margin-top-mm",
            "6",
            "--margin-bottom-mm",
            "4",
            "--margin-side-inch",
            "0.5",
            "--compact",
            "--auto-fit",
            "--auto-fit-max-trials",
            "9",
        ]
        with patch.object(sys, "argv", argv):
            args = parse_args()

        self.assertAlmostEqual(args.font_size_scale, 0.95)
        self.assertAlmostEqual(args.line_height_scale, 0.92)
        self.assertAlmostEqual(args.section_spacing_scale, 0.85)
        self.assertAlmostEqual(args.item_spacing_scale, 0.8)
        self.assertAlmostEqual(args.margin_top_mm, 6.0)
        self.assertAlmostEqual(args.margin_bottom_mm, 4.0)
        self.assertAlmostEqual(args.margin_side_inch, 0.5)
        self.assertTrue(args.compact)
        self.assertTrue(args.auto_fit)
        self.assertEqual(args.auto_fit_max_trials, 9)

    def test_parse_args_layout_defaults(self):
        argv = [
            "generate_final_resume.py",
            "--input-json",
            "cache/resume-working.json",
            "--output-file",
            "resume.pdf",
        ]
        with patch.object(sys, "argv", argv):
            args = parse_args()

        self.assertIsNone(args.font_size_scale)
        self.assertIsNone(args.line_height_scale)
        self.assertIsNone(args.section_spacing_scale)
        self.assertIsNone(args.item_spacing_scale)
        self.assertAlmostEqual(args.margin_top_mm, 5.0)
        self.assertAlmostEqual(args.margin_bottom_mm, 5.0)
        self.assertAlmostEqual(args.margin_side_inch, 0.6)
        self.assertFalse(args.compact)
        self.assertFalse(args.auto_fit)
        self.assertEqual(args.auto_fit_max_trials, 12)

    def test_parse_args_rejects_input_md(self):
        argv = [
            "generate_final_resume.py",
            "--input-md",
            "cache/resume-working.md",
            "--output-file",
            "resume.pdf",
        ]
        with patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit):
                parse_args()


if __name__ == "__main__":
    unittest.main()
