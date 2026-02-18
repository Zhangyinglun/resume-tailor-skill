import tempfile
import unittest
from pathlib import Path

from templates.layout_settings import LayoutSettings
from templates.modern_resume_template import (
    create_styles,
    generate_resume,
    register_fonts,
)


SAMPLE_CONTENT = {
    "name": "Test User",
    "contact": "City | test@example.com | linkedin.com/in/test",
    "summary": "Experienced engineer.",
    "skills": [{"category": "Languages", "items": "Python, Go"}],
    "experience": [
        {
            "company": "TestCorp",
            "title": "Engineer",
            "location": "Seattle",
            "dates": "2023-Present",
            "bullets": ["Built systems."],
        }
    ],
    "education": [{"school": "TestU", "degree": "M.S. CS", "dates": "2021-2023"}],
}


class LayoutIntegrationTest(unittest.TestCase):
    def test_create_styles_accepts_layout_settings(self):
        base_font, bold_font, _ = register_fonts()
        settings = LayoutSettings(font_size_scale=0.9)
        styles = create_styles(base_font, bold_font, layout=settings)
        self.assertAlmostEqual(styles["Header"].fontSize, 13.5, places=1)

    def test_create_styles_default_settings_unchanged(self):
        base_font, bold_font, _ = register_fonts()
        styles = create_styles(base_font, bold_font)
        self.assertAlmostEqual(styles["Header"].fontSize, 15.0, places=1)
        self.assertAlmostEqual(styles["Bullet"].fontSize, 9.85, places=2)

    def test_generate_resume_with_compact_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = LayoutSettings(compact_mode=True)
            output_path = generate_resume(
                "test_compact_resume.pdf",
                SAMPLE_CONTENT,
                base_dir=tmpdir,
                layout=settings,
            )
            self.assertTrue(Path(output_path).exists())

    def test_generate_resume_without_layout_backward_compatible(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = generate_resume(
                "test_default_resume.pdf",
                SAMPLE_CONTENT,
                base_dir=tmpdir,
            )
            self.assertTrue(Path(output_path).exists())


if __name__ == "__main__":
    unittest.main()
