import unittest

from templates.layout_settings import DEFAULT_SETTINGS, LayoutSettings


class LayoutSettingsTest(unittest.TestCase):
    def test_default_settings_have_expected_values(self):
        settings = DEFAULT_SETTINGS
        self.assertEqual(settings.font_size_scale, 1.0)
        self.assertEqual(settings.line_height_scale, 1.0)
        self.assertEqual(settings.section_spacing_scale, 1.0)
        self.assertEqual(settings.item_spacing_scale, 1.0)
        self.assertEqual(settings.margin_top_mm, 5.0)
        self.assertEqual(settings.margin_bottom_mm, 5.0)
        self.assertEqual(settings.margin_side_inch, 0.6)
        self.assertFalse(settings.compact_mode)

    def test_compact_mode_applies_smaller_scales(self):
        settings = LayoutSettings(compact_mode=True)
        self.assertLess(settings.effective_font_size_scale, 1.0)
        self.assertLess(settings.effective_line_height_scale, 1.0)
        self.assertLess(settings.effective_section_spacing_scale, 1.0)
        self.assertLess(settings.effective_item_spacing_scale, 1.0)

    def test_explicit_scales_override_compact_defaults(self):
        settings = LayoutSettings(compact_mode=True, font_size_scale=1.2)
        self.assertAlmostEqual(settings.effective_font_size_scale, 1.2)

    def test_scale_bounds_enforce_safe_range(self):
        too_small = LayoutSettings(font_size_scale=0.3)
        self.assertGreaterEqual(too_small.effective_font_size_scale, 0.7)

        too_big = LayoutSettings(font_size_scale=2.0)
        self.assertLessEqual(too_big.effective_font_size_scale, 1.3)


if __name__ == "__main__":
    unittest.main()
