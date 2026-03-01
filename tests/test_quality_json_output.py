import json
import unittest

from scripts.check_pdf_quality import build_quality_report

_DEFAULT_THRESHOLDS = {
    "min_bottom_mm": 3.0, "max_bottom_mm": 8.0,
    "min_top_mm": 3.0, "max_top_mm": 20.0,
    "min_side_mm": 10.0, "max_side_mm": 25.0,
}


def _build_report(*, page_count=1, margins=None, **overrides):
    defaults = dict(
        page_count=page_count,
        width_mm=210.0, height_mm=297.0,
        has_text=True, html_leak_count=0, placeholders=[],
        margins=margins or {"top": 5.0, "bottom": 5.0, "left": 15.0, "right": 15.0},
        missing_sections=[], missing_keywords=[], provided_keywords=[],
        contact={"email": True, "phone": True, "linkedin": False},
        layout_warnings=[], margin_thresholds=_DEFAULT_THRESHOLDS,
    )
    defaults.update(overrides)
    return build_quality_report(**defaults)


class QualityJsonOutputTest(unittest.TestCase):
    def test_build_quality_report_returns_complete_structure(self):
        report = _build_report(provided_keywords=["Python"])
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(len(report["checks"]), 12)
        for check in report["checks"]:
            self.assertIn("name", check)
            self.assertIn("passed", check)
            self.assertIn("detail", check)

    def test_build_quality_report_fails_on_multi_page(self):
        report = _build_report(page_count=2)
        self.assertEqual(report["verdict"], "NEED-ADJUSTMENT")

    def test_report_serializable_as_json(self):
        report = _build_report(margins=None)
        deserialized = json.loads(json.dumps(report, ensure_ascii=False))
        self.assertEqual(deserialized["verdict"], report["verdict"])


if __name__ == "__main__":
    unittest.main()
