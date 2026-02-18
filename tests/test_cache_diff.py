import tempfile
import unittest
from pathlib import Path

from scripts.resume_cache_manager import (
    diff_cache_against_template,
    init_base_template_from_text,
    init_working_from_template,
    update_cache_from_markdown,
)


SAMPLE_TEMPLATE = """John Doe
Seattle, WA | john@example.com | linkedin.com/in/johndoe

Summary
Backend engineer with 6 years in distributed systems.

Skills
Programming Languages: Python, Go, Java
Cloud: AWS, Kubernetes

Experience
Example Corp | Senior Engineer | Seattle, WA | 2021 - Present
- Built event pipeline, reduced latency by 35%.
- Implemented microservices architecture.
- Optimized database queries.

Education
Example University | M.S. in CS | 2018 - 2020
"""

MODIFIED_WORKING = """# HEADER
Name: John Doe
Contact: Seattle, WA | john@example.com | linkedin.com/in/johndoe

## SUMMARY
Senior backend engineer specializing in cloud-native distributed systems.

## TECHNICAL SKILLS
- Programming Languages: Python, Go, Kafka
- Cloud: AWS, Kubernetes, Docker

## PROFESSIONAL EXPERIENCE
### Example Corp | Senior Engineer | Seattle, WA | 2021 - Present
- Designed event-driven pipeline using Kafka, reduced latency by 35%.
- Implemented microservices architecture.

## EDUCATION
- Example University | M.S. in CS | 2018 - 2020
"""


class CacheDiffTest(unittest.TestCase):
    def test_diff_detects_section_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            init_base_template_from_text(workspace, SAMPLE_TEMPLATE)
            init_working_from_template(workspace)
            update_cache_from_markdown(workspace, MODIFIED_WORKING)

            result = diff_cache_against_template(workspace)

            self.assertIsInstance(result, dict)
            self.assertIn("summary", result)
            self.assertIn("skills", result)
            self.assertIn("experience", result)
            self.assertEqual(result["summary"]["status"], "modified")

    def test_diff_counts_bullet_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            init_base_template_from_text(workspace, SAMPLE_TEMPLATE)
            init_working_from_template(workspace)
            update_cache_from_markdown(workspace, MODIFIED_WORKING)

            result = diff_cache_against_template(workspace)

            experience = result["experience"]
            self.assertIn("bullet_count_template", experience)
            self.assertIn("bullet_count_working", experience)
            self.assertEqual(experience["bullet_count_template"], 3)
            self.assertEqual(experience["bullet_count_working"], 2)

    def test_diff_raises_when_no_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                diff_cache_against_template(workspace)


if __name__ == "__main__":
    unittest.main()
