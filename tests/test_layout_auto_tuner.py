import unittest

from scripts.layout_auto_tuner import (
    AutoFitTrial,
    CONTENT_CHECKS,
    LAYOUT_FIXABLE_CHECKS,
    _build_candidates,
    _diagnose_direction,
    _expand_candidates,
    _shrink_candidates,
    score_trial,
)
from templates.layout_settings import LayoutSettings


def _report(verdict: str, failed: set[str], overrides: dict | None = None) -> dict:
    """Build a minimal QC report.  *overrides* maps check name → detail dict."""
    overrides = overrides or {}
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
        detail = overrides.get(name, {})
        checks.append({"name": name, "passed": name not in failed, "detail": detail})
    return {"verdict": verdict, "checks": checks}


class ScoreTrialTest(unittest.TestCase):
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

    def test_score_prefers_closer_to_default_when_both_pass(self):
        """Among two PASS trials, prefer the one closer to 1.0 scales."""
        closer = AutoFitTrial(
            layout=LayoutSettings(
                compact_mode=True,
                font_size_scale=0.94,
                line_height_scale=0.92,
                section_spacing_scale=0.90,
                item_spacing_scale=0.86,
            ),
            report=_report("PASS", set()),
        )
        further = AutoFitTrial(
            layout=LayoutSettings(
                compact_mode=True,
                font_size_scale=0.84,
                line_height_scale=0.80,
                section_spacing_scale=0.72,
                item_spacing_scale=0.68,
            ),
            report=_report("PASS", set()),
        )
        self.assertGreater(score_trial(closer), score_trial(further))

    def test_score_readability_breaks_tie(self):
        """When compression distance is equal, prefer higher readability."""
        # 1.05 and 0.95 are equidistant from 1.0 but 1.05 is more readable
        expanded = AutoFitTrial(
            layout=LayoutSettings(font_size_scale=1.05, line_height_scale=1.05),
            report=_report("PASS", set()),
        )
        shrunk = AutoFitTrial(
            layout=LayoutSettings(font_size_scale=0.95, line_height_scale=0.95),
            report=_report("PASS", set()),
        )
        self.assertGreater(score_trial(expanded), score_trial(shrunk))

    def test_score_counts_only_layout_fixable_as_critical(self):
        """Content-only failures should not affect critical failure count."""
        # Both fail one check, but one is layout-fixable and the other is content-only
        layout_fail = AutoFitTrial(
            layout=LayoutSettings(),
            report=_report("NEED-ADJUSTMENT", {"bottom_margin"}),
        )
        content_fail = AutoFitTrial(
            layout=LayoutSettings(),
            report=_report("NEED-ADJUSTMENT", {"placeholder_content"}),
        )
        # Content fail should score higher (fewer layout-fixable critical failures)
        self.assertGreater(score_trial(content_fail), score_trial(layout_fail))


class DiagnoseDirectionTest(unittest.TestCase):
    def test_expand_when_bottom_margin_too_large(self):
        report = _report(
            "NEED-ADJUSTMENT",
            {"bottom_margin"},
            overrides={"bottom_margin": {"bottom_mm": 25.0}},
        )
        self.assertEqual(_diagnose_direction(report), "expand")

    def test_shrink_when_page_count_exceeds_one(self):
        report = _report(
            "NEED-ADJUSTMENT",
            {"page_count"},
            overrides={"page_count": {"count": 2}},
        )
        self.assertEqual(_diagnose_direction(report), "shrink")

    def test_shrink_when_bottom_margin_too_small(self):
        report = _report(
            "NEED-ADJUSTMENT",
            {"bottom_margin"},
            overrides={"bottom_margin": {"bottom_mm": 1.5}},
        )
        self.assertEqual(_diagnose_direction(report), "shrink")

    def test_pass_when_all_layout_checks_ok(self):
        # Only content check fails, all layout checks pass
        report = _report(
            "NEED-ADJUSTMENT",
            {"placeholder_content"},
        )
        self.assertEqual(_diagnose_direction(report), "pass")

    def test_page_count_overflow_takes_priority_over_large_bottom_margin(self):
        report = _report(
            "NEED-ADJUSTMENT",
            {"page_count", "bottom_margin"},
            overrides={
                "page_count": {"count": 2},
                "bottom_margin": {"bottom_mm": 50.0},
            },
        )
        self.assertEqual(_diagnose_direction(report), "shrink")


class BuildCandidatesTest(unittest.TestCase):
    def test_expand_direction_uses_expand_presets(self):
        candidates = _build_candidates(6, direction="expand")
        # First is default, rest are expansion (scales > 1.0)
        for c in candidates[1:]:
            self.assertGreaterEqual(c.effective_font_size_scale, 1.0)

    def test_shrink_direction_uses_shrink_presets(self):
        candidates = _build_candidates(10, direction="shrink")
        # Should contain compact candidates (scales < 1.0)
        has_compact = any(c.compact_mode for c in candidates)
        self.assertTrue(has_compact)

    def test_hint_inserted_as_first_candidate(self):
        hint = LayoutSettings(font_size_scale=1.15, line_height_scale=1.10)
        candidates = _build_candidates(5, hint=hint, direction="expand")
        self.assertEqual(candidates[0], hint)

    def test_hint_not_duplicated_if_already_present(self):
        default = LayoutSettings(compact_mode=False)
        candidates = _build_candidates(5, hint=default, direction="expand")
        self.assertEqual(candidates.count(default), 1)


class PresetsTest(unittest.TestCase):
    def test_expand_candidates_all_above_default(self):
        for c in _expand_candidates():
            self.assertGreater(c.effective_font_size_scale, 1.0)

    def test_shrink_candidates_all_below_default(self):
        for c in _shrink_candidates():
            self.assertLessEqual(c.effective_font_size_scale, 1.0)

    def test_check_sets_are_disjoint_and_cover_all(self):
        self.assertEqual(LAYOUT_FIXABLE_CHECKS & CONTENT_CHECKS, set())
        all_checks = LAYOUT_FIXABLE_CHECKS | CONTENT_CHECKS
        self.assertEqual(len(all_checks), 11)


if __name__ == "__main__":
    unittest.main()
