import json
import unittest

from scripts.check_pdf_quality import build_quality_report


class QualityJsonOutputTest(unittest.TestCase):
    def test_build_quality_report_returns_complete_structure(self):
        report = build_quality_report(
            page_count=1,
            width_mm=210.0,
            height_mm=297.0,
            has_text=True,
            html_leak_count=0,
            margins={"top": 5.0, "bottom": 5.0, "left": 15.0, "right": 15.0},
            missing_sections=[],
            contact={"email": True, "phone": True, "linkedin": False},
            missing_keywords=[],
            provided_keywords=["Python"],
            layout_warnings=[],
            margin_thresholds={
                "min_bottom_mm": 3.0,
                "max_bottom_mm": 8.0,
                "min_top_mm": 3.0,
                "max_top_mm": 20.0,
                "min_side_mm": 10.0,
                "max_side_mm": 25.0,
            },
        )

        self.assertIn("verdict", report)
        self.assertEqual(report["verdict"], "PASS")
        self.assertIn("checks", report)
        self.assertEqual(len(report["checks"]), 11)
        for check in report["checks"]:
            self.assertIn("name", check)
            self.assertIn("passed", check)
            self.assertIn("detail", check)

    def test_build_quality_report_fails_on_multi_page(self):
        report = build_quality_report(
            page_count=2,
            width_mm=210.0,
            height_mm=297.0,
            has_text=True,
            html_leak_count=0,
            margins={"top": 5.0, "bottom": 5.0, "left": 15.0, "right": 15.0},
            missing_sections=[],
            contact={"email": True, "phone": True, "linkedin": False},
            missing_keywords=[],
            provided_keywords=[],
            layout_warnings=[],
            margin_thresholds={
                "min_bottom_mm": 3.0,
                "max_bottom_mm": 8.0,
                "min_top_mm": 3.0,
                "max_top_mm": 20.0,
                "min_side_mm": 10.0,
                "max_side_mm": 25.0,
            },
        )
        self.assertEqual(report["verdict"], "NEED-ADJUSTMENT")

    def test_report_serializable_as_json(self):
        report = build_quality_report(
            page_count=1,
            width_mm=210.0,
            height_mm=297.0,
            has_text=True,
            html_leak_count=0,
            margins=None,
            missing_sections=[],
            contact={"email": True, "phone": True, "linkedin": False},
            missing_keywords=[],
            provided_keywords=[],
            layout_warnings=[],
            margin_thresholds={
                "min_bottom_mm": 3.0,
                "max_bottom_mm": 8.0,
                "min_top_mm": 3.0,
                "max_top_mm": 20.0,
                "min_side_mm": 10.0,
                "max_side_mm": 25.0,
            },
        )
        serialized = json.dumps(report, ensure_ascii=False)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["verdict"], report["verdict"])


if __name__ == "__main__":
    unittest.main()
