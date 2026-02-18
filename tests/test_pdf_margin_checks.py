import unittest

from scripts.check_pdf_quality import (
    estimate_page_margins_mm,
    margin_within_range,
    points_to_mm,
)


class _FakePage:
    def __init__(
        self, width: float, height: float, words: list[dict[str, float]]
    ) -> None:
        self.width = width
        self.height = height
        self._words = words

    def extract_words(self):
        return self._words


class PdfMarginChecksTest(unittest.TestCase):
    def test_estimate_page_margins_mm_returns_all_sides(self):
        page = _FakePage(
            width=600.0,
            height=800.0,
            words=[
                {"x0": 72.0, "x1": 528.0, "top": 36.0, "bottom": 760.0},
            ],
        )

        margins = estimate_page_margins_mm(page)
        self.assertIsNotNone(margins)
        self.assertAlmostEqual(margins["top"], points_to_mm(36.0), places=3)
        self.assertAlmostEqual(margins["bottom"], points_to_mm(40.0), places=3)
        self.assertAlmostEqual(margins["left"], points_to_mm(72.0), places=3)
        self.assertAlmostEqual(margins["right"], points_to_mm(72.0), places=3)

    def test_margin_within_range_checks_lower_and_upper_bounds(self):
        self.assertTrue(margin_within_range(6.0, minimum=3.0, maximum=8.0))
        self.assertFalse(margin_within_range(2.9, minimum=3.0, maximum=8.0))
        self.assertFalse(margin_within_range(8.1, minimum=3.0, maximum=8.0))


if __name__ == "__main__":
    unittest.main()
