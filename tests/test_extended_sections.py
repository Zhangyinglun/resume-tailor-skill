import tempfile
import unittest
from pathlib import Path

from scripts.resume_cache_manager import normalize_resume_text_to_markdown
from scripts.resume_md_to_json import markdown_to_content
from templates.modern_resume_template import generate_resume, validate_content


MARKDOWN_WITH_PROJECTS = """# HEADER
Name: Jane Smith
Contact: NY | jane@example.com | linkedin.com/in/jane

## SUMMARY
Full-stack engineer with 5 years experience.

## TECHNICAL SKILLS
- Languages: Python, TypeScript

## PROFESSIONAL EXPERIENCE
### Acme Inc | Engineer | NY | 2022 - Present
- Built web app serving 10K users.

## PROJECTS
### Open Source CLI Tool | Python, Click | 2023
- Created a CLI tool with 500+ GitHub stars.

## CERTIFICATIONS
- AWS Solutions Architect | Amazon | 2023
- CKA (Certified Kubernetes Administrator) | CNCF | 2022

## AWARDS
- Employee of the Year | Acme Inc | 2023

## EDUCATION
- NYU | B.S. Computer Science | 2018 - 2022
"""


class ExtendedSectionsParseTest(unittest.TestCase):
    def test_markdown_to_content_parses_projects(self):
        content = markdown_to_content(MARKDOWN_WITH_PROJECTS)
        self.assertIn("projects", content)
        self.assertEqual(len(content["projects"]), 1)
        self.assertEqual(content["projects"][0]["name"], "Open Source CLI Tool")
        self.assertIn("500+", content["projects"][0]["bullets"][0])

    def test_markdown_to_content_parses_certifications(self):
        content = markdown_to_content(MARKDOWN_WITH_PROJECTS)
        self.assertIn("certifications", content)
        self.assertEqual(len(content["certifications"]), 2)
        self.assertEqual(
            content["certifications"][0]["name"], "AWS Solutions Architect"
        )

    def test_markdown_to_content_parses_awards(self):
        content = markdown_to_content(MARKDOWN_WITH_PROJECTS)
        self.assertIn("awards", content)
        self.assertEqual(len(content["awards"]), 1)
        self.assertEqual(content["awards"][0]["name"], "Employee of the Year")

    def test_markdown_without_extended_sections_still_works(self):
        basic_md = """# HEADER
Name: Test
Contact: test@test.com

## SUMMARY
Engineer.

## TECHNICAL SKILLS
- Python

## PROFESSIONAL EXPERIENCE
### Corp | Dev | NYC | 2023
- Built things.

## EDUCATION
- School | Degree | 2020
"""
        content = markdown_to_content(basic_md)
        self.assertEqual(content["projects"], [])
        self.assertEqual(content["certifications"], [])
        self.assertEqual(content["awards"], [])

    def test_validate_content_accepts_extended_fields(self):
        content = markdown_to_content(MARKDOWN_WITH_PROJECTS)
        validate_content(content)

    def test_generate_resume_renders_extended_sections(self):
        content = markdown_to_content(MARKDOWN_WITH_PROJECTS)
        with tempfile.TemporaryDirectory() as tmpdir:
            output = generate_resume("test_extended.pdf", content, base_dir=tmpdir)
            self.assertTrue(Path(output).exists())


class NormalizeExtendedSectionsTest(unittest.TestCase):
    def test_normalize_preserves_projects_section(self):
        raw = """Jane Smith
NY | jane@example.com | linkedin.com/in/jane

Summary
Full-stack engineer.

Skills
Python, TypeScript

Experience
Acme Inc | Engineer | NY | 2022 - Present
- Built web app.

Projects
CLI Tool | Python | 2023
- Created CLI with 500+ stars.

Education
NYU | B.S. CS | 2018 - 2022
"""
        markdown = normalize_resume_text_to_markdown(raw)
        self.assertIn("## PROJECTS", markdown)


if __name__ == "__main__":
    unittest.main()
