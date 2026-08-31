from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

try:
    import pdfplumber
    import reportlab
except ImportError:  # pragma: no cover - dependency check reports this separately.
    pdfplumber = None
    reportlab = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.check_pdf_quality import build_quality_report
from scripts.evidence_ledger_manager import (
    initialize_workspace,
    rebuild_tailoring_manifest,
)


def sample_resume(*, invalid: bool = False) -> dict[str, Any]:
    bullets = [
        "Built distributed APIs using Python and AWS, reducing latency by 20%.",
        "Automated deployment validation with Python, preventing invalid releases.",
        "Designed recovery workflows across AWS services, improving resilience.",
        "Implemented request tracing with Python, enabling faster incident diagnosis.",
    ]
    return {
        "name": "[Company]" if invalid else "Alex Chen",
        "contact": (
            "missing"
            if invalid
            else "Seattle | +1 206-555-0100 | alex@example.com | linkedin.com/in/alex"
        ),
        "summary": "Backend engineer building distributed systems and cloud services.",
        "skills": [{"category": "Languages", "items": "Python, Go, C++"}],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "location": "Seattle",
                "dates": "2020 - Present",
                "bullets": bullets,
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "B.S. Computer Science",
                "dates": "2016 - 2020",
            }
        ],
    }


def prepare_audited_workspace(root: Path, resume: dict[str, Any]) -> Path:
    initialize_workspace(root, resume)
    rebuild_tailoring_manifest(root)
    return root / "cache" / "resume-working.json"


class PdfQualityPolicyTests(unittest.TestCase):
    def test_excess_whitespace_is_warning_not_failure(self) -> None:
        report = build_quality_report(
            page_count=1,
            width_mm=210.0,
            height_mm=297.0,
            has_text=True,
            html_leak_count=0,
            placeholders=[],
            margins={"top": 25.0, "bottom": 40.0, "left": 30.0, "right": 30.0},
            missing_sections=[],
            contact={"email": True, "phone": True, "linkedin": False},
            missing_keywords=[],
            provided_keywords=[],
            layout_warnings=[],
            margin_thresholds={
                "min_bottom_mm": 3.0,
                "max_bottom_mm": 8.0,
                "min_top_mm": 3.0,
                "max_top_mm": 20.0,
                "min_side_mm": 10.0,
                "max_side_mm": 25.0,
            },
        )
        self.assertEqual(report["verdict"], "PASS")
        warning_check = next(
            check for check in report["checks"] if check["name"] == "layout_warnings"
        )
        self.assertTrue(warning_check["detail"]["warnings"])


@unittest.skipIf(reportlab is None or pdfplumber is None, "PDF dependencies unavailable")
class PdfPipelineTests(unittest.TestCase):
    def test_renderer_rejects_skill_package_output(self) -> None:
        from templates.modern_resume_template import generate_resume

        repo_root = Path(__file__).resolve().parent.parent
        with self.assertRaisesRegex(ValueError, "outside the Skill package"):
            generate_resume(
                "resume.pdf",
                sample_resume(),
                base_dir=str(repo_root / "resume_output"),
            )

    def test_renderer_escapes_user_markup(self) -> None:
        from scripts.check_pdf_quality import check_pdf_file
        from templates.modern_resume_template import generate_resume

        assert pdfplumber is not None
        resume = sample_resume()
        resume["summary"] = "Built R&D services with Java Map<K,V> and C++ & C#."
        with tempfile.TemporaryDirectory() as temp_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                output = Path(generate_resume("resume.pdf", resume, base_dir=temp_dir))
            self.assertTrue(output.exists())
            with pdfplumber.open(output) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            self.assertIn("Map<K,V>", text)
            self.assertIn("R&D", text)
            report = check_pdf_file(output)
            html_check = next(check for check in report["checks"] if check["name"] == "html_leak")
            self.assertTrue(html_check["passed"])
            geometry_check = next(
                check for check in report["checks"] if check["name"] == "text_geometry"
            )
            self.assertIn("sparse_trailing_line_count", geometry_check["detail"])

    def test_renderer_supports_itemized_skills(self) -> None:
        from templates.modern_resume_template import generate_resume

        assert pdfplumber is not None
        resume = sample_resume()
        resume["skills"] = [
            {
                "category": "AI Platforms & Tooling",
                "items": ["Azure OpenAI", "MCP", "RAG"],
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                rendered_path = Path(generate_resume("skills-array.pdf", resume, base_dir=temp_dir))
            self.assertTrue(rendered_path.exists())
            with pdfplumber.open(rendered_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            self.assertIn("AI Platforms & Tooling", text)
            self.assertIn("Azure OpenAI, MCP, RAG", text)

    def test_generator_blocks_when_mandatory_audit_inputs_are_missing(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "resume.json"
            source.write_text(json.dumps(sample_resume()), encoding="utf-8")
            output_dir = root / "output"
            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
            ]
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                result = cli.main()

            self.assertEqual(result, 1)
            self.assertIn("factual audit", stderr.getvalue().lower())
            self.assertFalse((output_dir / "resume.pdf").exists())

    def test_generator_rejects_output_dir_inside_skill_package(self) -> None:
        import scripts.generate_final_resume as cli

        repo_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temp_dir:
            source = prepare_audited_workspace(Path(temp_dir), sample_resume())
            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(repo_root / "resume_output"),
            ]
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                result = cli.main()

            self.assertEqual(result, 1)
            self.assertIn("outside the Skill package", stderr.getvalue())

    def test_failed_candidate_preserves_existing_pdfs(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            output_dir.mkdir()
            current = output_dir / "resume.pdf"
            other = output_dir / "previous-good.pdf"
            current.write_bytes(b"accepted-current")
            other.write_bytes(b"accepted-other")
            source = prepare_audited_workspace(root, sample_resume(invalid=True))

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 2)
            self.assertEqual(current.read_bytes(), b"accepted-current")
            self.assertEqual(other.read_bytes(), b"accepted-other")
            self.assertTrue(list((output_dir / "rejected").glob("*.pdf")))

    def test_passing_candidate_archives_then_publishes(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            output_dir.mkdir()
            current = output_dir / "resume.pdf"
            current.write_bytes(b"accepted-current")
            source = prepare_audited_workspace(root, sample_resume())

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
                "--auto-fit",
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 0)
            self.assertTrue(current.read_bytes().startswith(b"%PDF"))
            self.assertTrue(list((output_dir / "backup").rglob("resume_old_*.pdf")))

    def test_generator_accepts_valid_warning_disposition(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            # 2 bullets in 1 experience entry triggers bullet_density advisory warning
            sparse_resume = sample_resume()
            sparse_resume["experience"][0]["bullets"] = [
                "Built reliable APIs using Python, improving system uptime.",
                "Automated release testing with Python, preventing failed rollouts.",
            ]
            source = prepare_audited_workspace(root, sparse_resume)

            # Add valid disposition
            manifest_path = root / "cache" / "resume-changes.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["warning_dispositions"] = [
                {
                    "finding": "bullet_density",
                    "status": "accepted",
                    "reason": "Compact resume format accepted for this target position.",
                }
            ]
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
                "--auto-fit",
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 0)
            self.assertTrue((output_dir / "resume.pdf").exists())

    def test_generator_blocks_disposition_with_empty_reason_or_wrong_finding(self) -> None:
        import scripts.generate_final_resume as cli

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            sparse_resume = sample_resume()
            sparse_resume["experience"][0]["bullets"] = [
                "Built reliable APIs using Python, improving system uptime.",
                "Automated release testing with Python, preventing failed rollouts.",
            ]
            source = prepare_audited_workspace(root, sparse_resume)
            manifest_path = root / "cache" / "resume-changes.json"

            # 1. Empty reason should block
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["warning_dispositions"] = [
                {"finding": "bullet_density", "status": "accepted", "reason": "   "}
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(source),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
                result = cli.main()
            self.assertEqual(result, 2)

            # 2. Mismatched finding name should block
            manifest["warning_dispositions"] = [
                {"finding": "unrelated_check", "status": "accepted", "reason": "Valid reason"}
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
                result = cli.main()
            self.assertEqual(result, 2)

    def test_generator_publishes_model_projected_resume(self) -> None:
        import scripts.generate_final_resume as cli
        from scripts.projection_plan_manager import build_projection
        from scripts.resume_shared import canonical_json_fingerprint, write_json_file

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sparse_resume = sample_resume()
            init_res = initialize_workspace(root, sparse_resume)
            snapshot = init_res["source_snapshot"]
            ledger = init_res["evidence_ledger"]

            exp_entity = next(e for e in ledger["entities"] if e["entity_type"] == "experience")
            exp_bullet_claims = [
                c["claim_id"] for c in exp_entity["claims"] if c["claim_type"] == "achievement"
            ]
            skill_entities = [e for e in ledger["entities"] if e["entity_type"] == "skill"]
            skill_item_claim = next(
                c["claim_id"]
                for e in skill_entities
                for c in e["claims"]
                if c["claim_type"] == "technology"
            )
            profile_entity = next(e for e in ledger["entities"] if e["entity_type"] == "profile")
            summary_claim = profile_entity["claims"][0]["claim_id"]

            jd_data: dict[str, Any] = {
                "position": "Backend Engineer",
                "keywords": {"P1": ["Python"], "P2": ["Go"], "P3": []},
                "capabilities": [
                    {
                        "capability_id": "cap-backend",
                        "priority": "P1",
                        "name": "Backend Python Development",
                        "match_type": "direct",
                        "evidence_state": "sourced",
                        "claim_ids": [],
                    }
                ],
                "alignment": {"matched": ["cap-backend"], "transferable": [], "gaps": []},
            }
            write_json_file(root / "cache" / "jd-analysis.json", jd_data)

            plan: dict[str, Any] = {
                "schema_version": 1,
                "revision": 1,
                "status": "ready",
                "target_jd_fingerprint": canonical_json_fingerprint(jd_data),
                "source_snapshot_fingerprint": snapshot["source_fingerprint"],
                "constraints": {
                    "page_size": "A4",
                    "page_count": 1,
                    "experience_bullet_min": 1,
                    "experience_bullet_max": 5,
                    "skills_group_min": 2,
                    "skills_group_max": 4,
                    "skills_rendered_line_min": 2,
                    "skills_rendered_line_max": 4,
                    "clarification_question_max": 5,
                    "content_fit_revision_max": 3,
                },
                "clarifications": [],
                "summary_intent": {
                    "intent_id": "intent-summary",
                    "claim_ids": [summary_claim],
                    "capability_ids": ["cap-backend"],
                    "operation": "REWORD",
                    "content_intent": "Backend engineer building distributed systems.",
                    "target_lines": 1,
                },
                "experience_plans": [
                    {
                        "entity_id": exp_entity["entity_id"],
                        "importance": "critical",
                        "target_bullet_count": 2,
                        "reason": "Direct backend evidence.",
                        "content_intents": [
                            {
                                "intent_id": "intent-bullet-1",
                                "claim_ids": [exp_bullet_claims[0]],
                                "capability_ids": ["cap-backend"],
                                "operation": "REWORD",
                                "content_intent": "Built distributed APIs using Python and AWS, reducing latency by 20%.",
                                "target_lines": 1,
                            },
                            {
                                "intent_id": "intent-bullet-2",
                                "claim_ids": [exp_bullet_claims[1]],
                                "capability_ids": ["cap-backend"],
                                "operation": "REWORD",
                                "content_intent": "Automated deployment validation with Python, preventing invalid releases.",
                                "target_lines": 1,
                            },
                        ],
                    }
                ],
                "skills_plan": {
                    "groups": [
                        {
                            "category": "Languages",
                            "items": [
                                {
                                    "display_term": "Python",
                                    "claim_ids": [skill_item_claim],
                                    "capability_ids": ["cap-backend"],
                                    "basis": "Direct match",
                                },
                                {
                                    "display_term": "Go",
                                    "claim_ids": [skill_item_claim],
                                    "capability_ids": ["cap-backend"],
                                    "basis": "Direct match",
                                },
                            ],
                        },
                        {
                            "category": "Systems",
                            "items": [
                                {
                                    "display_term": "C++",
                                    "claim_ids": [skill_item_claim],
                                    "capability_ids": ["cap-backend"],
                                    "basis": "Direct match",
                                },
                                {
                                    "display_term": "Python",
                                    "claim_ids": [skill_item_claim],
                                    "capability_ids": ["cap-backend"],
                                    "basis": "Direct match",
                                },
                            ],
                        },
                    ]
                },
                "warning_dispositions": [
                    {
                        "finding": "bullet_density",
                        "status": "accepted",
                        "reason": "Compact format for single target position.",
                    }
                ],
            }

            language: dict[str, Any] = {
                "schema_version": 1,
                "plan_revision": 1,
                "target_jd_fingerprint": canonical_json_fingerprint(jd_data),
                "items": [
                    {
                        "intent_id": "intent-summary",
                        "source_claim_ids": [summary_claim],
                        "rendered_text": "Backend engineer building distributed systems and cloud services.",
                        "meaning_check": {
                            "facts_added": [],
                            "facts_removed": [],
                            "metrics_changed": [],
                            "ownership_changed": False,
                        },
                    },
                    {
                        "intent_id": "intent-bullet-1",
                        "source_claim_ids": [exp_bullet_claims[0]],
                        "rendered_text": "Built distributed APIs using Python and AWS, reducing latency by 20%.",
                        "meaning_check": {
                            "facts_added": [],
                            "facts_removed": [],
                            "metrics_changed": [],
                            "ownership_changed": False,
                        },
                    },
                    {
                        "intent_id": "intent-bullet-2",
                        "source_claim_ids": [exp_bullet_claims[1]],
                        "rendered_text": "Automated deployment validation with Python, preventing invalid releases.",
                        "meaning_check": {
                            "facts_added": [],
                            "facts_removed": [],
                            "metrics_changed": [],
                            "ownership_changed": False,
                        },
                    },
                ],
            }

            plan_path = root / "cache" / "projection-plan.json"
            language_path = root / "cache" / "projection-language.json"
            write_json_file(plan_path, plan)
            write_json_file(language_path, language)

            build_res = build_projection(root, plan_path, language_path)
            self.assertEqual(build_res.status, "built")

            output_dir = root / "output"
            argv = [
                "generate_final_resume.py",
                "--input-json",
                str(root / "cache" / "resume-working.json"),
                "--output-file",
                "resume.pdf",
                "--output-dir",
                str(output_dir),
                "--auto-fit",
            ]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                result = cli.main()

            self.assertEqual(result, 0)
            self.assertTrue((output_dir / "resume.pdf").exists())



if __name__ == "__main__":
    unittest.main()
