import tempfile
import unittest
from pathlib import Path

from scripts.resume_cache_manager import (
    has_base_template,
    init_base_template_from_text,
    init_cache_from_text,
    init_working_from_template,
    read_base_template_json,
    read_cache_json,
    reset_cache_on_start,
    update_cache_from_json,
)


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

SAMPLE_TAB_DELIMITED_TEXT = """YINGLUN ZHANG
+1 (206) 670-6349 | yinglunzhangwork@gmail.com | Redmond, WA, USA | linkedin.com/in/yinglun-zhang

SUMMARY
Senior Software Engineer with 8+ years building AI and data platforms.

PROFESSIONAL EXPERIENCE
Microsoft | Software Engineer\tRedmond, WA | Sep 2024 - Sep 2025
• Built fault-tolerant AI automation reducing manual ticket handling by 85%.

EDUCATION
Northeastern University | Master of Science in Data Science, GPA: 3.97/4.0\tSep 2021 - Jun 2023
Coursework: Machine Learning, Neural Networks, Deep Learning
Shanghai University | Bachelor of Science in Computer Science\tSep 2012 - Jul 2016

TECHNICAL SKILLS
Languages & Frameworks: Go, Java, Python
"""


class ResumeCacheFlowTest(unittest.TestCase):
    def test_init_update_read_and_cleanup_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            created_path = init_cache_from_text(workspace, SAMPLE_SOURCE_TEXT)
            self.assertTrue(created_path.exists())

            payload = read_cache_json(workspace)
            self.assertEqual(payload["name"], "John Doe")

            payload["summary"] = (
                "Staff backend engineer with 6 years in distributed systems."
            )
            update_cache_from_json(workspace, payload)

            updated = read_cache_json(workspace)
            self.assertIn("Staff backend engineer", updated["summary"])
            self.assertTrue(updated["experience"])

            self.assertTrue(reset_cache_on_start(workspace))
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
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            self.assertFalse(has_base_template(workspace))

            template_path = init_base_template_from_text(
                workspace, SAMPLE_DETAILED_TEMPLATE
            )
            self.assertTrue(template_path.exists())
            self.assertTrue(has_base_template(workspace))

            template_content = read_base_template_json(workspace)
            self.assertIn("summary", template_content)
            self.assertIn("Experienced backend engineer", template_content["summary"])

            working_path = init_working_from_template(workspace)
            self.assertTrue(working_path.exists())

            working_content = read_cache_json(workspace)
            self.assertEqual(template_content, working_content)

            reset_cache_on_start(workspace)
            self.assertFalse(working_path.exists())
            self.assertTrue(template_path.exists())

    def test_template_init_without_existing_template_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                init_working_from_template(workspace)

    def test_init_handles_tab_delimited_experience_and_education(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            init_cache_from_text(workspace, SAMPLE_TAB_DELIMITED_TEXT)

            payload = read_cache_json(workspace)
            self.assertEqual(payload["experience"][0]["company"], "Microsoft")
            self.assertEqual(payload["experience"][0]["title"], "Software Engineer")
            self.assertEqual(payload["experience"][0]["location"], "Redmond, WA")
            self.assertEqual(payload["experience"][0]["dates"], "Sep 2024 - Sep 2025")

            self.assertEqual(
                payload["education"][0]["school"], "Northeastern University"
            )
            self.assertEqual(
                payload["education"][0]["degree"],
                "Master of Science in Data Science, GPA: 3.97/4.0",
            )
            self.assertEqual(payload["education"][0]["dates"], "Sep 2021 - Jun 2023")
            self.assertEqual(len(payload["education"]), 2)
            self.assertEqual(payload["education"][1]["school"], "Shanghai University")
            self.assertEqual(
                payload["education"][1]["degree"],
                "Bachelor of Science in Computer Science",
            )
            self.assertEqual(payload["education"][1]["dates"], "Sep 2012 - Jul 2016")


if __name__ == "__main__":
    unittest.main()
