from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts.evidence_ledger_manager import initialize_workspace
from scripts.projection_plan_manager import (
    BuildResult,
    build_projection,
    main,
    validate_language_output,
    validate_projection_plan,
)
from scripts.resume_shared import canonical_json_fingerprint, load_json_file, write_json_file


def sample_resume() -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": "Backend engineer building scalable systems.",
        "skills": [
            {"category": "Platforms", "items": ["Azure OpenAI", "MCP"]},
            {"category": "Languages", "items": ["Python", "Go"]},
        ],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "location": "Seattle",
                "dates": "2020 - Present",
                "bullets": [
                    "Implemented an MCP tool-calling workflow with Azure OpenAI.",
                    "Optimized cache latency by 40% across distributed nodes.",
                ],
            }
        ],
        "projects": [],
        "education": [
            {
                "school": "Example University",
                "degree": "B.S. Computer Science",
                "dates": "2020",
            }
        ],
        "certifications": [],
        "awards": [],
    }


def sample_jd() -> dict[str, Any]:
    return {
        "position": "Applied AI Engineer",
        "keywords": {"P1": ["MCP"], "P2": ["Azure OpenAI"], "P3": []},
        "capabilities": [
            {
                "capability_id": "cap-mcp",
                "priority": "P1",
                "name": "MCP tool integration",
                "match_type": "direct",
                "evidence_state": "sourced",
                "claim_ids": [],
            },
            {
                "capability_id": "cap-azure",
                "priority": "P2",
                "name": "Azure OpenAI integration",
                "match_type": "direct",
                "evidence_state": "sourced",
                "claim_ids": [],
            },
        ],
        "alignment": {"matched": [], "transferable": [], "gaps": []},
    }


class ProjectionPlanManagerTests(unittest.TestCase):
    def make_workspace_and_plan(
        self,
        temp_dir: str,
        status: str = "ready",
        resume: dict[str, Any] | None = None,
        jd: dict[str, Any] | None = None,
    ) -> tuple[Path, dict[str, Any]]:
        workspace = Path(temp_dir)
        resume_data = sample_resume() if resume is None else resume
        jd_data = sample_jd() if jd is None else jd

        init_result = initialize_workspace(workspace, resume_data)
        snapshot = init_result["source_snapshot"]
        ledger = init_result["evidence_ledger"]

        cache_dir = workspace / "cache"
        write_json_file(cache_dir / "jd-analysis.json", jd_data)

        exp_entity = next(e for e in ledger["entities"] if e["entity_type"] == "experience")
        exp_bullet_claims = [
            c["claim_id"] for c in exp_entity["claims"] if c["claim_type"] == "achievement"
        ]
        skill_entities = [e for e in ledger["entities"] if e["entity_type"] == "skill"]
        skill_claims = [
            c["claim_id"]
            for e in skill_entities
            for c in e["claims"]
            if ".items[" in str(c.get("provenance", {}).get("source_path", ""))
        ]
        profile_entity = next(e for e in ledger["entities"] if e["entity_type"] == "profile")
        summary_claim = profile_entity["claims"][0]["claim_id"]

        plan: dict[str, Any] = {
            "schema_version": 1,
            "revision": 1,
            "status": status,
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
                "capability_ids": ["cap-mcp"],
                "operation": "REWORD",
                "content_intent": "Backend engineer with applied AI focus.",
                "target_lines": 2,
            },
            "experience_plans": [
                {
                    "entity_id": exp_entity["entity_id"],
                    "importance": "critical",
                    "target_bullet_count": 2,
                    "reason": "Carries direct P1/P2 evidence.",
                    "content_intents": [
                        {
                            "intent_id": "intent-exp-1",
                            "claim_ids": [exp_bullet_claims[0]],
                            "capability_ids": ["cap-mcp", "cap-azure"],
                            "operation": "EMPHASIZE",
                            "content_intent": "Lead MCP tool-calling integration on Azure OpenAI.",
                            "target_lines": 2,
                        },
                        {
                            "intent_id": "intent-exp-2",
                            "claim_ids": [exp_bullet_claims[1]],
                            "capability_ids": [],
                            "operation": "KEEP",
                            "content_intent": "Cache latency optimization.",
                            "target_lines": 1,
                        },
                    ],
                }
            ],
            "skills_plan": {
                "groups": [
                    {
                        "category": "Platforms",
                        "target_lines": 1,
                        "items": [
                            {
                                "display_term": "Azure OpenAI",
                                "claim_ids": [skill_claims[0]],
                                "capability_ids": ["cap-azure"],
                                "basis": "P2 direct capability",
                            },
                            {
                                "display_term": "MCP",
                                "claim_ids": [skill_claims[1]],
                                "capability_ids": ["cap-mcp"],
                                "basis": "P1 direct capability",
                            },
                        ],
                    },
                    {
                        "category": "Languages",
                        "target_lines": 1,
                        "items": [
                            {
                                "display_term": "Python",
                                "claim_ids": [skill_claims[2]],
                                "capability_ids": [],
                                "basis": "Core language",
                            },
                            {
                                "display_term": "Go",
                                "claim_ids": [skill_claims[3]],
                                "capability_ids": [],
                                "basis": "Core language",
                            },
                        ],
                    },
                ]
            },
            "optional_sections": [],
            "next_cuts": [],
        }

        if status == "needs_clarification":
            plan["clarifications"] = [
                {
                    "question_id": "q-evals",
                    "capability_ids": ["cap-mcp"],
                    "question": "Did the platform include a repeatable evaluation suite?",
                }
            ]

        return workspace, plan

    def make_ready_artifacts(self, temp_dir: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        workspace, plan = self.make_workspace_and_plan(temp_dir)
        language = {
            "schema_version": 1,
            "plan_revision": 1,
            "target_jd_fingerprint": plan["target_jd_fingerprint"],
            "items": [
                {
                    "intent_id": intent["intent_id"],
                    "rendered_text": {
                        "intent-summary": "Backend engineer building scalable systems.",
                        "intent-exp-1": "Implemented an MCP tool-calling workflow with Azure OpenAI.",
                        "intent-exp-2": "Optimized cache latency by 40% across distributed nodes.",
                    }[intent["intent_id"]],
                    "source_claim_ids": copy.deepcopy(intent["claim_ids"]),
                    "style_actions": ["concise_resume_language"],
                    "meaning_check": {
                        "facts_added": [],
                        "facts_removed": [],
                        "metrics_changed": [],
                        "ownership_changed": False,
                    },
                }
                for intent in [
                    plan["summary_intent"],
                    *plan["experience_plans"][0]["content_intents"],
                ]
            ],
        }
        return workspace, plan, language

    def test_language_output_requires_exactly_one_record_per_intent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan, language = self.make_ready_artifacts(temp_dir)
            language["items"].pop()

            with self.assertRaisesRegex(ValueError, "missing intent"):
                validate_language_output(
                    plan,
                    language,
                    load_json_file(workspace / "cache" / "candidate-evidence.json"),
                )

    def test_language_output_rejects_changed_claim_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan, language = self.make_ready_artifacts(temp_dir)
            language["items"][0]["source_claim_ids"] = ["claim-unknown"]

            with self.assertRaisesRegex(ValueError, "claim links"):
                validate_language_output(
                    plan,
                    language,
                    load_json_file(workspace / "cache" / "candidate-evidence.json"),
                )

    def test_language_output_rejects_invalid_metadata_and_records(self) -> None:
        mutations = {
            "plan revision": lambda plan, language: language.update(plan_revision=2),
            "JD fingerprint": lambda plan, language: language.update(target_jd_fingerprint="stale"),
            "duplicate intent": lambda plan, language: language["items"].append(
                copy.deepcopy(language["items"][0])
            ),
            "extra intent": lambda plan, language: language["items"].append(
                {**copy.deepcopy(language["items"][0]), "intent_id": "extra"}
            ),
        }
        for expected, mutate in mutations.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                workspace, plan, language = self.make_ready_artifacts(temp_dir)
                mutate(plan, language)
                with self.assertRaisesRegex(ValueError, expected):
                    validate_language_output(
                        plan,
                        language,
                        load_json_file(workspace / "cache" / "candidate-evidence.json"),
                    )

    def test_language_output_rejects_unsafe_text_and_meaning_changes(self) -> None:
        mutations = {
            "facts_added": lambda item: item["meaning_check"]["facts_added"].append("new"),
            "facts_removed": lambda item: item["meaning_check"]["facts_removed"].append("old"),
            "metrics_changed": lambda item: item["meaning_check"]["metrics_changed"].append("40%"),
            "ownership_changed": lambda item: item["meaning_check"].update(ownership_changed=True),
            "rendered text": lambda item: item.update(rendered_text=" "),
            "first-person": lambda item: item.update(rendered_text="I built it"),
            "chatbot": lambda item: item.update(rendered_text="I hope this helps"),
            "placeholder": lambda item: item.update(rendered_text="[To be filled later]"),
            "HTML placeholder": lambda item: item.update(rendered_text="<!-- TODO -->"),
        }
        for expected, mutate in mutations.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                workspace, plan, language = self.make_ready_artifacts(temp_dir)
                mutate(language["items"][0])
                with self.assertRaisesRegex(ValueError, expected):
                    validate_language_output(
                        plan,
                        language,
                        load_json_file(workspace / "cache" / "candidate-evidence.json"),
                    )

    def test_revision_rejects_unrelated_wording_drift_and_missing_previous_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, previous_plan, previous_language = self.make_ready_artifacts(temp_dir)
            plan = copy.deepcopy(previous_plan)
            language = copy.deepcopy(previous_language)
            plan["revision"] = 2
            language["plan_revision"] = 2
            language["items"][0]["rendered_text"] = "Different wording."
            ledger = load_json_file(workspace / "cache" / "candidate-evidence.json")
            with self.assertRaisesRegex(ValueError, "unrelated wording drift"):
                validate_language_output(
                    plan,
                    language,
                    ledger,
                    previous_plan=previous_plan,
                    previous_language=previous_language,
                )
            with self.assertRaisesRegex(ValueError, "previous"):
                validate_language_output(plan, language, ledger)

    def test_invalid_language_does_not_replace_existing_projection_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan, language = self.make_ready_artifacts(temp_dir)
            cache = workspace / "cache"
            plan_path = cache / "projection-plan.json"
            language_path = cache / "projection-language.json"
            write_json_file(plan_path, plan)
            language["items"].pop()
            write_json_file(language_path, language)
            old_resume = {"sentinel": "resume"}
            old_manifest = {"sentinel": "manifest"}
            write_json_file(cache / "resume-working.json", old_resume)
            write_json_file(cache / "resume-changes.json", old_manifest)

            with self.assertRaises(ValueError):
                build_projection(workspace, plan_path, language_path)

            self.assertEqual(load_json_file(cache / "resume-working.json"), old_resume)
            self.assertEqual(load_json_file(cache / "resume-changes.json"), old_manifest)

    def test_build_materializes_audited_projection_manifest_and_last_built_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan, language = self.make_ready_artifacts(temp_dir)
            cache = workspace / "cache"
            plan_path = cache / "projection-plan.json"
            language_path = cache / "projection-language.json"
            write_json_file(plan_path, plan)
            write_json_file(language_path, language)

            result = build_projection(workspace, plan_path, language_path)

            self.assertEqual(result.status, "built")
            resume = load_json_file(cache / "resume-working.json")
            manifest = load_json_file(cache / "resume-changes.json")
            self.assertEqual(resume["summary"], language["items"][0]["rendered_text"])
            self.assertEqual(resume["experience"][0]["company"], "Example Corp")
            self.assertEqual(len(resume["experience"][0]["bullets"]), 2)
            self.assertEqual(manifest["resume_fingerprint"], canonical_json_fingerprint(resume))
            self.assertEqual(load_json_file(cache / "projection-plan.last-built.json"), plan)
            self.assertEqual(
                load_json_file(cache / "projection-language.last-built.json"), language
            )

    def test_build_cli_outputs_paths_and_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan, language = self.make_ready_artifacts(temp_dir)
            plan_path = workspace / "cache" / "projection-plan.json"
            language_path = workspace / "cache" / "projection-language.json"
            write_json_file(plan_path, plan)
            write_json_file(language_path, language)
            with patch(
                "sys.argv",
                [
                    "projection_plan_manager.py",
                    "build",
                    "--workspace",
                    str(workspace),
                    "--plan",
                    str(plan_path),
                    "--language",
                    str(language_path),
                ],
            ):
                with patch("sys.stdout", new=io.StringIO()) as stdout:
                    self.assertEqual(main(), 0)
                    output = json.loads(stdout.getvalue())
            self.assertEqual(output["status"], "built")
            self.assertEqual(
                output["resume_path"],
                str((workspace / "cache" / "resume-working.json").resolve()),
            )

    def test_needs_clarification_returns_questions_without_building(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir, status="needs_clarification")
            result = validate_projection_plan(workspace, plan)

            self.assertEqual(result["status"], "needs_clarification")
            self.assertEqual(len(result["clarifications"]), 1)
            self.assertEqual(result["clarifications"][0]["question_id"], "q-evals")

    def test_ready_plan_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir, status="ready")
            result = validate_projection_plan(workspace, plan)

            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["clarifications"], [])
            self.assertEqual(result["intent_count"], 3)  # summary + 2 exp intents

    def test_more_than_5_clarifications_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir, status="needs_clarification")
            plan["clarifications"] = [
                {
                    "question_id": f"q-{i}",
                    "capability_ids": ["cap-mcp"],
                    "question": f"Question {i}?",
                }
                for i in range(6)
            ]

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("clarification", str(ctx.exception).lower())

    def test_needs_clarification_with_empty_clarifications_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir, status="needs_clarification")
            plan["clarifications"] = []

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("clarification", str(ctx.exception).lower())

    def test_stale_jd_fingerprint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["target_jd_fingerprint"] = "sha256:stale-jd-hash"

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("stale jd", str(ctx.exception).lower())

    def test_stale_source_snapshot_fingerprint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["source_snapshot_fingerprint"] = "sha256:stale-snapshot-hash"

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("stale source snapshot", str(ctx.exception).lower())

    def test_missing_formal_experience_entity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["experience_plans"] = []

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("experience", str(ctx.exception).lower())

    def test_target_bullet_count_out_of_range_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["experience_plans"][0]["target_bullet_count"] = 0
            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("target_bullet_count", str(ctx.exception))

            plan["experience_plans"][0]["target_bullet_count"] = 6
            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("target_bullet_count", str(ctx.exception))

    def test_skill_groups_count_out_of_range_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            # 1 group fails
            plan["skills_plan"]["groups"] = [plan["skills_plan"]["groups"][0]]
            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("skills", str(ctx.exception).lower())

            # 5 groups fails
            group_template = plan["skills_plan"]["groups"][0]
            plan["skills_plan"]["groups"] = [copy.deepcopy(group_template) for _ in range(5)]
            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("skills", str(ctx.exception).lower())

    def test_unknown_or_inactive_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["experience_plans"][0]["content_intents"][0]["claim_ids"] = ["claim-non-existent"]

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("claim", str(ctx.exception).lower())

    def test_revoked_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            ledger_path = workspace / "cache" / "candidate-evidence.json"
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            # Revoke first claim
            exp_entity = next(e for e in ledger["entities"] if e["entity_type"] == "experience")
            bullet_claim = next(c for c in exp_entity["claims"] if c["claim_type"] == "achievement")
            bullet_claim["status"] = "revoked"
            bullet_claim["revoked_at"] = "2026-08-29T12:00:00Z"
            write_json_file(ledger_path, ledger)

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("claim", str(ctx.exception).lower())

    def test_unknown_capability_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["experience_plans"][0]["content_intents"][0]["capability_ids"] = ["cap-unknown"]

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("capability", str(ctx.exception).lower())

    def test_content_intent_mixing_entities_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            # Put summary claim and experience claim into the same experience content intent
            summary_claim = plan["summary_intent"]["claim_ids"][0]
            exp_claim = plan["experience_plans"][0]["content_intents"][0]["claim_ids"][0]
            plan["experience_plans"][0]["content_intents"][0]["claim_ids"] = [
                exp_claim,
                summary_claim,
            ]

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertTrue(
                "entit" in str(ctx.exception).lower() or "mix" in str(ctx.exception).lower()
            )

    def test_duplicate_intent_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            # Duplicate intent-exp-1
            plan["experience_plans"][0]["content_intents"][1]["intent_id"] = "intent-exp-1"

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("duplicate intent_id", str(ctx.exception).lower())

    def test_revision_exceeding_max_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["revision"] = 4

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("revision", str(ctx.exception).lower())

    def test_invalid_status_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir)
            plan["status"] = "unknown_status"

            with self.assertRaises(ValueError) as ctx:
                validate_projection_plan(workspace, plan)
            self.assertIn("status", str(ctx.exception).lower())

    def test_build_result_structure(self) -> None:
        result = BuildResult(
            status="ready",
            resume_path=Path("/tmp/resume.json"),
            manifest_path=Path("/tmp/manifest.json"),
            clarifications=(),
        )
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.resume_path, Path("/tmp/resume.json"))
        self.assertEqual(result.manifest_path, Path("/tmp/manifest.json"))
        self.assertEqual(result.clarifications, ())

    def test_cli_validate_ready_and_clarification_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace, plan = self.make_workspace_and_plan(temp_dir, status="ready")
            plan_path = workspace / "cache" / "projection-plan.json"
            write_json_file(plan_path, plan)

            # Ready plan CLI returns 0
            with patch(
                "sys.argv",
                [
                    "projection_plan_manager.py",
                    "validate",
                    "--workspace",
                    str(workspace),
                    "--plan",
                    str(plan_path),
                ],
            ):
                with patch("sys.stdout", new=io.StringIO()) as stdout:
                    exit_code = main()
                    self.assertEqual(exit_code, 0)
                    out = json.loads(stdout.getvalue())
                    self.assertEqual(out["status"], "ready")

            # Clarification plan CLI returns 2
            plan["status"] = "needs_clarification"
            plan["clarifications"] = [
                {
                    "question_id": "q-1",
                    "capability_ids": ["cap-mcp"],
                    "question": "Evaluation suite?",
                }
            ]
            write_json_file(plan_path, plan)

            with patch(
                "sys.argv",
                [
                    "projection_plan_manager.py",
                    "validate",
                    "--workspace",
                    str(workspace),
                    "--plan",
                    str(plan_path),
                ],
            ):
                with patch("sys.stdout", new=io.StringIO()) as stdout:
                    exit_code = main()
                    self.assertEqual(exit_code, 2)
                    out = json.loads(stdout.getvalue())
                    self.assertEqual(out["status"], "needs_clarification")

            # Invalid plan CLI returns 1
            plan["revision"] = 99
            write_json_file(plan_path, plan)

            with patch(
                "sys.argv",
                [
                    "projection_plan_manager.py",
                    "validate",
                    "--workspace",
                    str(workspace),
                    "--plan",
                    str(plan_path),
                ],
            ):
                with patch("sys.stderr", new=io.StringIO()) as stderr:
                    exit_code = main()
                    self.assertEqual(exit_code, 1)
                    self.assertIn("revision", stderr.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
