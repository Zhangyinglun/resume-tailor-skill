from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.audit_factual_integrity import audit_resume
from scripts.check_content_quality import run_all_checks
from scripts.check_pdf_geometry import build_content_fit_feedback
from scripts.check_pdf_quality import check_pdf_file
from scripts.evidence_ledger_manager import initialize_workspace
from scripts.projection_plan_manager import build_projection
from scripts.resume_shared import (
    canonical_json_fingerprint,
    load_json_file,
    write_json_file,
)
from templates.modern_resume_template import generate_resume


def synthetic_resume() -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "Seattle, WA | alex@example.com | +1 206-555-0100",
        "summary": "Software engineer building AI diagnostics and distributed APIs.",
        "skills": [
            {"category": "AI", "items": "Azure OpenAI, MCP, RAG, Evals"},
            {"category": "Backend", "items": "Java, Go, Python, Kafka, Redis, Kubernetes"},
        ],
        "experience": [
            {
                "company": "Example Cloud",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "dates": "2024 - Present",
                "bullets": [
                    "Built an MCP diagnostic workflow on Azure OpenAI with tool calling.",
                    "Created RAG evaluations for incident diagnostics.",
                ],
            },
            {
                "company": "Example Social",
                "title": "Software Engineer",
                "location": "Seattle, WA",
                "dates": "2021 - 2024",
                "bullets": [
                    "Built Go APIs serving 10M daily requests on Kubernetes.",
                    "Reduced data latency with Kafka and Redis.",
                ],
            },
            {
                "company": "Example Commerce",
                "title": "Software Engineer",
                "location": "Beijing, China",
                "dates": "2018 - 2021",
                "bullets": [
                    "Built Java services handling 20K QPS with high availability.",
                ],
            },
        ],
        "awards": [
            {
                "name": "Synthetic Distributed Scheduling Patent",
                "organization": "Example Commerce",
                "dates": "2021",
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "B.S. Computer Science",
                "dates": "2018",
                "location": "Seattle, WA",
            }
        ],
    }


def build_fixture_projection(
    workspace: Path,
    jd_name: str,
    plan_name: str,
    language_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture_root = Path(__file__).resolve().parent / "fixtures" / "projection"
    jd = load_json_file(fixture_root / jd_name)
    write_json_file(workspace / "cache" / "jd-analysis.json", jd)
    snapshot = load_json_file(workspace / "cache" / "base-resume.json")
    ledger = load_json_file(workspace / "cache" / "candidate-evidence.json")
    active_ids = {
        str(claim["claim_id"])
        for entity in ledger["entities"]
        for claim in entity["claims"]
        if entity["state"] == "active" and claim["status"] == "active"
    }

    plan = load_json_file(fixture_root / plan_name)
    referenced_ids = {
        str(claim_id)
        for experience in plan["experience_plans"]
        for intent in experience["content_intents"]
        for claim_id in intent["claim_ids"]
    }
    referenced_ids.update(
        str(claim_id)
        for group in plan["skills_plan"]["groups"]
        for item in group["items"]
        for claim_id in item["claim_ids"]
    )
    if not referenced_ids <= active_ids:
        raise AssertionError(
            f"Fixture references unknown claims: {sorted(referenced_ids - active_ids)}"
        )

    plan["target_jd_fingerprint"] = canonical_json_fingerprint(jd)
    plan["source_snapshot_fingerprint"] = str(snapshot["source_fingerprint"])
    language = load_json_file(fixture_root / language_name)
    language["target_jd_fingerprint"] = plan["target_jd_fingerprint"]
    plan_path = workspace / "cache" / "projection-plan.json"
    language_path = workspace / "cache" / "projection-language.json"
    write_json_file(plan_path, plan)
    write_json_file(language_path, language)
    result = build_projection(workspace, plan_path, language_path)
    if result.status != "built":
        raise AssertionError(f"Projection did not build: {result.status}")
    return (
        load_json_file(workspace / "cache" / "resume-working.json"),
        load_json_file(workspace / "cache" / "resume-changes.json"),
    )


class ProjectionEndToEndTests(unittest.TestCase):
    def test_same_ledger_produces_distinct_ai_and_distributed_projections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialize_workspace(workspace, synthetic_resume())

            ai_resume, ai_manifest = build_fixture_projection(
                workspace,
                "jd-applied-ai.json",
                "plan-applied-ai.json",
                "language-applied-ai.json",
            )
            distributed_resume, distributed_manifest = build_fixture_projection(
                workspace,
                "jd-distributed-systems.json",
                "plan-distributed-systems.json",
                "language-distributed-systems.json",
            )

            ai_skills = {
                item
                for group in ai_resume["skills"]
                for item in group["items"]
            }
            distributed_skills = {
                item
                for group in distributed_resume["skills"]
                for item in group["items"]
            }
            self.assertIn("MCP", ai_skills)
            self.assertIn("Evals", ai_skills)
            self.assertNotIn("Evals", distributed_skills)
            self.assertIn("Kafka", distributed_skills)
            self.assertNotEqual(ai_skills, distributed_skills)
            self.assertTrue(all(entry["bullets"] for entry in ai_resume["experience"]))
            self.assertTrue(all(entry["bullets"] for entry in distributed_resume["experience"]))
            ledger = load_json_file(workspace / "cache" / "candidate-evidence.json")
            base_resume = load_json_file(workspace / "cache" / "base-resume.json")
            self.assertEqual(
                audit_resume(
                    ai_resume,
                    ai_manifest,
                    ledger,
                    base_resume=base_resume,
                )["verdict"],
                "PASS",
            )
            self.assertEqual(
                audit_resume(
                    distributed_resume,
                    distributed_manifest,
                    ledger,
                    base_resume=base_resume,
                )["verdict"],
                "PASS",
            )

    def test_ai_and_distributed_pdf_generation_and_geometry_quality(self) -> None:
        projections = [
            (
                "Applied AI",
                "jd-applied-ai.json",
                "plan-applied-ai.json",
                "language-applied-ai.json",
                "resume-ai.pdf",
            ),
            (
                "Distributed Systems",
                "jd-distributed-systems.json",
                "plan-distributed-systems.json",
                "language-distributed-systems.json",
                "resume-dist.pdf",
            ),
        ]
        for name, jd_file, plan_file, lang_file, pdf_name in projections:
            with self.subTest(projection=name):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workspace = Path(temp_dir)
                    initialize_workspace(workspace, synthetic_resume())
                    resume, manifest = build_fixture_projection(
                        workspace, jd_file, plan_file, lang_file
                    )
                    ledger = load_json_file(workspace / "cache" / "candidate-evidence.json")
                    base_resume = load_json_file(workspace / "cache" / "base-resume.json")

                    # 1. factual audit PASS
                    audit_report = audit_resume(
                        resume, manifest, ledger, base_resume=base_resume
                    )
                    self.assertEqual(audit_report["verdict"], "PASS")

                    # 2. run_all_checks() has no undisposed warnings
                    qc_findings = [
                        check
                        for check in run_all_checks(resume)
                        if check["status"] != "PASS"
                    ]
                    dispositions = {
                        str(item.get("finding")): item
                        for item in manifest.get("warning_dispositions", [])
                        if isinstance(item, dict)
                        and item.get("status") == "accepted"
                        and str(item.get("reason", "")).strip()
                    }
                    unresolved = [
                        f for f in qc_findings if f["name"] not in dispositions
                    ]
                    self.assertEqual(
                        unresolved,
                        [],
                        f"Found undisposed QC warnings in {name}: {unresolved}",
                    )

                    # 3. generate temporary PDF
                    output_dir = workspace / "output"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    pdf_path = Path(
                        generate_resume(pdf_name, resume, base_dir=str(output_dir))
                    )
                    self.assertTrue(pdf_path.exists())

                    # 4. check_pdf_file() PASS
                    qa_report = check_pdf_file(pdf_path)
                    self.assertEqual(
                        qa_report["verdict"],
                        "PASS",
                        f"PDF QA failed for {name}: {qa_report}",
                    )

                    # 5. build_content_fit_feedback() page_count is 1
                    feedback = build_content_fit_feedback(
                        pdf_path, resume, plan_revision=1
                    )
                    self.assertEqual(feedback["page_count"], 1)

                    # 6. Skills body line count is 2–4
                    skills_lines = int(
                        feedback["section_geometry"].get("skills", {}).get("line_count", 0)
                    )
                    self.assertTrue(
                        2 <= skills_lines <= 4,
                        f"Skills line count {skills_lines} not in range 2-4 for {name}",
                    )


if __name__ == "__main__":
    unittest.main()
