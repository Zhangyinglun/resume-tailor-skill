import tempfile
import unittest
from pathlib import Path

from scripts.resume_cache_manager import init_cache_from_text, read_cache_json
from templates.modern_resume_template import generate_resume, validate_content


CONTENT_WITH_PROJECTS = {
    "name": "Jane Smith",
    "contact": "NY | jane@example.com | linkedin.com/in/jane",
    "summary": "Full-stack engineer with 5 years experience.",
    "skills": [{"category": "Languages", "items": "Python, TypeScript"}],
    "experience": [
        {
            "company": "Acme Inc",
            "title": "Engineer",
            "location": "NY",
            "dates": "2022 - Present",
            "bullets": ["Built web app serving 10K users."],
        }
    ],
    "projects": [
        {
            "name": "Open Source CLI Tool",
            "tech": "Python, Click",
            "dates": "2023",
            "bullets": ["Created a CLI tool with 500+ GitHub stars."],
        }
    ],
    "certifications": [
        {"name": "AWS Solutions Architect", "issuer": "Amazon", "dates": "2023"},
        {
            "name": "CKA (Certified Kubernetes Administrator)",
            "issuer": "CNCF",
            "dates": "2022",
        },
    ],
    "awards": [
        {"name": "Employee of the Year", "organization": "Acme Inc", "dates": "2023"}
    ],
    "education": [
        {"school": "NYU", "degree": "B.S. Computer Science", "dates": "2018 - 2022"}
    ],
}


class ExtendedSectionsJsonTest(unittest.TestCase):
    def test_validate_content_accepts_extended_fields(self):
        validate_content(CONTENT_WITH_PROJECTS)

    def test_generate_resume_renders_extended_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = generate_resume(
                "test_extended.pdf", CONTENT_WITH_PROJECTS, base_dir=tmpdir
            )
            self.assertTrue(Path(output).exists())


class NormalizeExtendedSectionsTest(unittest.TestCase):
    def test_init_from_text_preserves_projects_section(self):
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
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            init_cache_from_text(workspace, raw)
            payload = read_cache_json(workspace)

        self.assertEqual(len(payload["projects"]), 1)
        self.assertEqual(payload["projects"][0]["name"], "CLI Tool")


if __name__ == "__main__":
    unittest.main()
