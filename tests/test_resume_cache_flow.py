import tempfile
import unittest
from pathlib import Path

from scripts.resume_cache_manager import (
    cleanup_cache,
    has_base_template,
    init_base_template_from_text,
    init_cache_from_text,
    init_working_from_template,
    read_base_template_markdown,
    reset_cache_on_start,
    update_cache_from_markdown,
)
from scripts.resume_md_to_json import markdown_to_content


SAMPLE_SOURCE_TEXT = """John Doe
Seattle, WA | john@example.com | linkedin.com/in/johndoe

Summary
Backend engineer with 6 years in distributed systems.

Skills
Python, Go, Kafka, AWS

Experience
Example Corp | Senior Engineer | Seattle, WA | 2021 - Present
- Built event pipeline, reduced latency by 35%.

Education
Example University | M.S. in CS | 2018 - 2020
"""

SAMPLE_DETAILED_TEMPLATE = """John Doe
Seattle, WA | john@example.com | linkedin.com/in/johndoe

Summary
Experienced backend engineer with 6 years building distributed systems. Expert in Python and Go. Led cross-functional teams to deliver scalable microservices.

Skills
Programming Languages: Python, Go, Java, JavaScript
Cloud & DevOps: AWS, Kubernetes, Docker, Terraform
Data Platform: Kafka, PostgreSQL, Redis, Elasticsearch

Experience
Example Corp | Senior Engineer | Seattle, WA | 2021 - Present
- Built event-driven pipeline using Kafka and Python, reduced latency by 35%.
- Implemented microservices architecture with Kubernetes, serving 100K+ requests per day.
- Led team of 4 engineers to deliver CI/CD automation using Jenkins and Terraform.
- Optimized database queries, improved response time by 50%.

Another Corp | Software Engineer | Boston, MA | 2018 - 2021
- Developed RESTful APIs using Go and PostgreSQL.
- Deployed applications to AWS using Docker containers.
- Mentored 2 junior engineers on best practices.

Education
Example University | M.S. in Computer Science | 2018 - 2020
"""


class ResumeCacheFlowTest(unittest.TestCase):
    def test_init_update_parse_and_cleanup_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            created_path = init_cache_from_text(workspace, SAMPLE_SOURCE_TEXT)
            self.assertTrue(created_path.exists())
            self.assertIn("## SUMMARY", created_path.read_text(encoding="utf-8"))

            updated_markdown = created_path.read_text(encoding="utf-8").replace(
                "Backend engineer", "Staff backend engineer"
            )
            update_cache_from_markdown(workspace, updated_markdown)

            parsed = markdown_to_content(updated_markdown)
            self.assertEqual(parsed["name"], "John Doe")
            self.assertIn("Staff backend engineer", parsed["summary"])
            self.assertTrue(parsed["experience"])

            self.assertTrue(cleanup_cache(workspace))
            self.assertFalse(created_path.exists())

    def test_reset_cache_on_start_removes_previous_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            cache_path = init_cache_from_text(workspace, SAMPLE_SOURCE_TEXT)
            self.assertTrue(cache_path.exists())

            deleted = reset_cache_on_start(workspace)
            self.assertTrue(deleted)
            self.assertFalse(cache_path.exists())

    def test_base_template_lifecycle(self):
        """Test complete lifecycle of long-term template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Template does not exist initially
            self.assertFalse(has_base_template(workspace))

            # Initialize long-term template
            template_path = init_base_template_from_text(
                workspace, SAMPLE_DETAILED_TEMPLATE
            )
            self.assertTrue(template_path.exists())
            self.assertTrue(has_base_template(workspace))

            # Read template content
            template_content = read_base_template_markdown(workspace)
            self.assertIn("## SUMMARY", template_content)
            self.assertIn("Experienced backend engineer", template_content)

            # Initialize working cache from template
            working_path = init_working_from_template(workspace)
            self.assertTrue(working_path.exists())

            working_content = working_path.read_text(encoding="utf-8")
            self.assertEqual(template_content, working_content)

            # Cleanup working cache does not affect long-term template
            cleanup_cache(workspace)
            self.assertFalse(working_path.exists())
            self.assertTrue(template_path.exists())

    def test_template_init_without_existing_template_raises_error(self):
        """Test that calling init_working_from_template without a template raises an exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                init_working_from_template(workspace)


if __name__ == "__main__":
    unittest.main()
