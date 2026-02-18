import unittest

from scripts.layout_auto_tuner import AutoFitTrial, score_trial
from templates.layout_settings import LayoutSettings


def _report(verdict: str, failed: set[str]) -> dict:
    checks = []
    for name in [
        "page_count",
        "page_size",
        "text_layer",
        "html_leak",
        "placeholder_content",
        "bottom_margin",
        "top_margin",
        "side_margins",
        "section_completeness",
        "contact_info",
        "keyword_coverage",
    ]:
        checks.append({"name": name, "passed": name not in failed, "detail": {}})
    return {"verdict": verdict, "checks": checks}


class LayoutAutoTunerTest(unittest.TestCase):
    def test_score_prefers_pass_over_need_adjustment(self):
        pass_trial = AutoFitTrial(
            layout=LayoutSettings(compact_mode=True),
            report=_report("PASS", set()),
        )
        fail_trial = AutoFitTrial(
            layout=LayoutSettings(compact_mode=False),
            report=_report("NEED-ADJUSTMENT", {"page_count"}),
        )

        self.assertGreater(score_trial(pass_trial), score_trial(fail_trial))

    def test_score_prefers_higher_readability_when_both_pass(self):
        more_readable = AutoFitTrial(
            layout=LayoutSettings(
                compact_mode=True,
                font_size_scale=0.94,
                line_height_scale=0.92,
                section_spacing_scale=0.90,
                item_spacing_scale=0.86,
            ),
            report=_report("PASS", set()),
        )
        more_compressed = AutoFitTrial(
            layout=LayoutSettings(
                compact_mode=True,
                font_size_scale=0.84,
                line_height_scale=0.80,
                section_spacing_scale=0.72,
                item_spacing_scale=0.68,
            ),
            report=_report("PASS", set()),
        )

        self.assertGreater(score_trial(more_readable), score_trial(more_compressed))


if __name__ == "__main__":
    unittest.main()
