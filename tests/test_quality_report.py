from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.generate_quality_report import (
    build_keyword_coverage,
    format_content_fit_section,
    format_language_optimization_section,
    format_projection_plan_section,
    generate_report,
)


class QualityReportTests(unittest.TestCase):
    def test_coverage_uses_boundaries_and_all_evidence_sections(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com | +1 206-555-0100",
            "summary": "Maintained distributed services.",
            "skills": [{"category": "Languages", "items": "Python"}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Software Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built reliable APIs using Python."],
                }
            ],
            "projects": [
                {
                    "name": "Runtime",
                    "tech": "Go, C++",
                    "dates": "2024",
                    "bullets": ["Built a local runtime in Go."],
                }
            ],
            "education": [
                {
                    "school": "Example University",
                    "degree": "B.S. Computer Science",
                    "dates": "2020",
                }
            ],
        }
        jd = {"keywords": {"P1": ["AI", "Go", "C++"], "P2": [], "P3": []}}
        coverage = build_keyword_coverage(resume, jd)["P1"]
        by_keyword = {entry["keyword"]: entry for entry in coverage}
        self.assertFalse(by_keyword["ai"]["covered"])
        self.assertTrue(by_keyword["go"]["covered"])
        self.assertTrue(by_keyword["c++"]["covered"])
        self.assertIn("projects[0].tech", by_keyword["c++"]["location"])

    def test_report_includes_factual_audit_coverage_and_findings(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com | +1 206-555-0100",
            "summary": "Engineer",
            "skills": [{"category": "Languages", "items": "Python"}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built services using Python, improving reliability."],
                }
            ],
            "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
        }
        factual_report = {
            "verdict": "FAIL",
            "coverage": {"covered_fields": 9, "total_fields": 10, "coverage_percent": 90.0},
            "findings": [
                {
                    "code": "UNSUPPORTED_METRIC",
                    "severity": "ERROR",
                    "path": "experience[0].bullets[0]",
                    "message": "Metric is unsupported.",
                }
            ],
        }

        report = generate_report(resume, None, factual_report=factual_report)

        self.assertIn("Factual Integrity", report)
        self.assertIn("90.0%", report)
        self.assertIn("UNSUPPORTED_METRIC", report)

    def test_report_includes_projection_language_and_content_fit_sections(self) -> None:
        resume = {
            "name": "Alex Chen",
            "contact": "alex@example.com | +1 206-555-0100",
            "summary": "Backend engineer.",
            "skills": [{"category": "AI Platforms", "items": ["MCP", "RAG"]}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": ["Built an MCP integration for service diagnostics."],
                }
            ],
            "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
        }
        jd_analysis = {
            "position": "Applied AI Engineer",
            "keywords": {"P1": ["MCP"], "P2": ["RAG"], "P3": []},
            "capabilities": [],
            "alignment": {"matched": [], "transferable": [], "gaps": []},
        }
        report = generate_report(
            resume,
            jd_analysis,
            projection_plan={
                "revision": 2,
                "experience_plans": [
                    {
                        "entity_id": "experience-example",
                        "importance": "critical",
                        "target_bullet_count": 4,
                        "reason": "Carries direct P1 evidence.",
                    }
                ],
                "optional_sections": [
                    {
                        "section": "awards",
                        "decision": "remove",
                        "reason": "Duplicates selected experience evidence.",
                    }
                ],
                "skills_plan": {
                    "groups": [
                        {"category": "AI Platforms", "items": [{"display_term": "MCP"}]}
                    ]
                },
            },
            language_output={
                "items": [
                    {
                        "intent_id": "intent-1",
                        "style_actions": ["remove_template_language"],
                        "meaning_check": {
                            "facts_added": [],
                            "facts_removed": [],
                            "metrics_changed": [],
                            "ownership_changed": False,
                        },
                    }
                ]
            },
            content_fit_feedback={
                "plan_revision": 2,
                "verdict": "fit",
                "page_count": 1,
                "bottom_whitespace_mm": 7.5,
                "issues": [],
            },
        )

        self.assertIn("Projection Plan", report)
        self.assertIn("critical", report)
        self.assertIn("Removed optional sections", report)
        self.assertIn("Resume Language Optimization", report)
        self.assertIn("remove_template_language", report)
        self.assertIn("Content Fit", report)
        self.assertIn("7.5", report)

    def test_format_projection_plan_section_with_retained_and_removed(self) -> None:
        plan = {
            "revision": 1,
            "status": "ready",
            "experience_plans": [
                {
                    "entity_id": "exp-1",
                    "importance": "high",
                    "target_bullet_count": 3,
                    "reason": "Core backend experience.",
                }
            ],
            "skills_plan": {
                "groups": [
                    {"category": "Languages", "items": ["Python", "Go"]},
                    {"category": "Databases", "items": [{"display_term": "PostgreSQL"}]},
                ]
            },
            "optional_sections": [
                {"section": "projects", "decision": "keep", "reason": "Demonstrates Go."},
                {"section": "awards", "decision": "remove", "reason": "Redundant."},
            ],
        }
        section = format_projection_plan_section(plan)
        self.assertIn("Plan revision: 1", section)
        self.assertIn("Status: ready", section)
        self.assertIn("exp-1", section)
        self.assertIn("Languages", section)
        self.assertIn("Python, Go", section)
        self.assertIn("Databases", section)
        self.assertIn("PostgreSQL", section)
        self.assertIn("Removed optional sections: awards (Redundant.)", section)
        self.assertIn("Retained optional sections: projects (Demonstrates Go.)", section)

    def test_format_language_optimization_section_warning_on_meaning_change(self) -> None:
        lang_output = {
            "items": [
                {
                    "intent_id": "intent-1",
                    "style_actions": ["tighten_verbs", "remove_template_language"],
                    "meaning_check": {
                        "facts_added": ["Extra fact"],
                        "facts_removed": [],
                        "metrics_changed": [],
                        "ownership_changed": False,
                    },
                },
                {
                    "intent_id": "intent-2",
                    "style_actions": ["tighten_verbs"],
                    "meaning_check": {
                        "facts_added": [],
                        "facts_removed": [],
                        "metrics_changed": [],
                        "ownership_changed": False,
                    },
                },
            ]
        }
        section = format_language_optimization_section(lang_output)
        self.assertIn("Total language items: 2", section)
        self.assertIn("Meaning changes detected", section)
        self.assertIn("tighten_verbs (2)", section)
        self.assertIn("remove_template_language (1)", section)

    def test_format_content_fit_section_details(self) -> None:
        feedback = {
            "plan_revision": 3,
            "verdict": "revision_required",
            "page_count": 2,
            "bottom_whitespace_mm": None,
            "section_geometry": {
                "skills": {"line_count": 5, "height_pt": 60.0},
            },
            "issues": ["skills_rendered_line_budget", "page_overflow"],
            "sparse_trailing_bullets": [{"line": "end"}],
        }
        section = format_content_fit_section(feedback)
        self.assertIn("Verdict: **revision_required**", section)
        self.assertIn("Plan revision: 3", section)
        self.assertIn("Page count: 2", section)
        self.assertIn("Bottom whitespace: —", section)
        self.assertIn("Skills line count: 5", section)
        self.assertIn("skills_rendered_line_budget, page_overflow", section)
        self.assertIn("Sparse trailing bullets detected: 1", section)

    def test_cli_execution_with_projection_and_language_and_content_fit(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        resume_data = {
            "name": "Alex Chen",
            "contact": "alex@example.com",
            "summary": "Experienced engineer maintaining distributed systems.",
            "skills": [{"category": "AI Platforms", "items": ["MCP"]}],
            "experience": [
                {
                    "company": "Example",
                    "title": "Engineer",
                    "dates": "2020 - Present",
                    "bullets": [
                        "Architected MCP integration for service diagnostics.",
                        "Implemented automated telemetry collectors across clusters.",
                        "Optimized retrieval pipelines reducing latency by 40%.",
                    ],
                }
            ],
            "education": [{"school": "Example", "degree": "B.S.", "dates": "2020"}],
        }
        jd_data = {
            "position": "Applied AI Engineer",
            "keywords": {"P1": ["MCP"], "P2": [], "P3": []},
            "capabilities": [],
            "alignment": {"matched": [], "transferable": [], "gaps": []},
        }
        plan_data = {
            "revision": 1,
            "experience_plans": [
                {
                    "entity_id": "exp-1",
                    "importance": "critical",
                    "target_bullet_count": 2,
                    "reason": "P1 match",
                }
            ],
            "skills_plan": {
                "groups": [{"category": "AI Platforms", "items": [{"display_term": "MCP"}]}]
            },
            "optional_sections": [],
        }
        lang_data = {
            "items": [
                {
                    "intent_id": "intent-1",
                    "style_actions": ["clarify_scope"],
                    "meaning_check": {
                        "facts_added": [],
                        "facts_removed": [],
                        "metrics_changed": [],
                        "ownership_changed": False,
                    },
                }
            ]
        }
        fit_data = {
            "plan_revision": 1,
            "verdict": "fit",
            "page_count": 1,
            "bottom_whitespace_mm": 5.0,
            "issues": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resume_file = temp_path / "resume.json"
            jd_file = temp_path / "jd.json"
            plan_file = temp_path / "plan.json"
            lang_file = temp_path / "lang.json"
            fit_file = temp_path / "fit.json"

            resume_file.write_text(json.dumps(resume_data), encoding="utf-8")
            jd_file.write_text(json.dumps(jd_data), encoding="utf-8")
            plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
            lang_file.write_text(json.dumps(lang_data), encoding="utf-8")
            fit_file.write_text(json.dumps(fit_data), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "generate_quality_report.py"),
                    "--resume",
                    str(resume_file),
                    "--jd-analysis",
                    str(jd_file),
                    "--projection-plan",
                    str(plan_file),
                    "--language-output",
                    str(lang_file),
                    "--content-fit-feedback",
                    str(fit_file),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Projection Plan", result.stdout)
            self.assertIn("Resume Language Optimization", result.stdout)
            self.assertIn("Content Fit", result.stdout)




if __name__ == "__main__":
    unittest.main()
