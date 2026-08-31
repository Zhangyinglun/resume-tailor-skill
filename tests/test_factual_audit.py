from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.audit_factual_integrity import audit_resume
from scripts.evidence_ledger_manager import (
    initialize_workspace,
    rebuild_tailoring_manifest,
)
from scripts.resume_shared import canonical_json_fingerprint


def sample_resume() -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": "Backend engineer building retrieval systems.",
        "skills": [{"category": "Platforms", "items": "Redis, Python"}],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "location": "Seattle",
                "dates": "2020 - Present",
                "bullets": ["Implemented a Redis cache serving 3,000 QPS."],
            }
        ],
        "projects": [],
        "education": [
            {"school": "Example University", "degree": "B.S. Computer Science", "dates": "2020"}
        ],
        "certifications": [],
        "awards": [],
    }


class FactualAuditTests(unittest.TestCase):
    def test_grounded_projection_with_complete_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            rebuilt = rebuild_tailoring_manifest(workspace)

            report = audit_resume(
                sample_resume(),
                rebuilt["manifest"],
                initialized["evidence_ledger"],
                base_resume=initialized["source_snapshot"],
            )

            self.assertEqual(report["verdict"], "PASS")
            self.assertEqual(report["findings"], [])
            self.assertEqual(
                report["coverage"]["covered_fields"], report["coverage"]["total_fields"]
            )

    def test_fabricated_metric_is_blocked_even_when_manifest_references_a_real_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]
            resume = sample_resume()
            resume["experience"][0]["bullets"][0] = "Implemented a Redis cache serving 5,000 QPS."
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)
            entry = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry["rendered_text"] = resume["experience"][0]["bullets"][0]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("UNSUPPORTED_METRIC", {item["code"] for item in report["findings"]})

    def test_tool_substitution_and_role_inflation_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]
            resume = sample_resume()
            resume["experience"][0]["bullets"][0] = "Led a NATS cache serving 3,000 QPS."
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)
            entry = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry["rendered_text"] = resume["experience"][0]["bullets"][0]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertIn("TOOL_DRIFT", codes)
            self.assertIn("ROLE_INFLATION", codes)

    def test_entity_bound_fields_require_an_explicit_entity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]
            entry = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry["entity_id"] = None

            report = audit_resume(sample_resume(), manifest, initialized["evidence_ledger"])

            self.assertIn(
                "MISSING_ENTITY_BINDING",
                {item["code"] for item in report["findings"]},
            )

    def test_declared_strict_semantic_normalization_can_reuse_prior_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]
            resume = sample_resume()
            resume["summary"] = "Backend engineer building RAG systems."
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)
            entry = next(
                item for item in manifest["entries"] if item["projection_path"] == "summary"
            )
            entry["rendered_text"] = resume["summary"]
            entry["match_type"] = "semantic_equivalent"
            entry["semantic_normalizations"] = [
                {
                    "term": "RAG",
                    "basis": "The sourced summary describes retrieval systems and the sourced experience describes retrieval before use.",
                }
            ]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])

            self.assertEqual(report["verdict"], "PASS")

    def test_unresolved_evidence_and_incomplete_manifest_are_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]
            manifest["entries"] = [
                entry for entry in manifest["entries"] if entry["projection_path"] != "contact"
            ]
            summary_entry = next(
                entry for entry in manifest["entries"] if entry["projection_path"] == "summary"
            )
            summary_claim_id = summary_entry["source_claim_ids"][0]
            for entity in initialized["evidence_ledger"]["entities"]:
                for claim in entity["claims"]:
                    if claim["claim_id"] == summary_claim_id:
                        claim["evidence_state"] = "needs_confirmation"

            report = audit_resume(sample_resume(), manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertIn("MISSING_MANIFEST_ENTRY", codes)
            self.assertIn("UNRESOLVED_EVIDENCE", codes)

    def test_english_go_phrase_does_not_trigger_tool_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            resume = sample_resume()
            resume["experience"][0]["bullets"][0] = (
                "Created a go-to-market brief for Python services."
            )
            initialized = initialize_workspace(workspace, resume)
            rebuilt = rebuild_tailoring_manifest(workspace)

            report = audit_resume(
                resume,
                rebuilt["manifest"],
                initialized["evidence_ledger"],
                base_resume=initialized["source_snapshot"],
            )

            self.assertEqual(report["verdict"], "PASS")

    def test_lexical_variants_do_not_trigger_tool_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base_resume = sample_resume()
            base_resume["experience"][0]["bullets"][0] = "Built a REST API in Python."
            initialized = initialize_workspace(workspace, base_resume)
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            resume = sample_resume()
            resume["experience"][0]["bullets"][0] = "Built a RESTful API in Python."
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)
            entry = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry["rendered_text"] = resume["experience"][0]["bullets"][0]

            report = audit_resume(
                resume,
                manifest,
                initialized["evidence_ledger"],
            )

            self.assertEqual(report["verdict"], "PASS")

    def test_tool_drift_rejects_substring_known_tech_and_scope_substitutions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base = sample_resume()
            base["experience"][0]["bullets"] = [
                "Built user interfaces with JavaScript.",
                "Managed relational databases with MySQL.",
                "Ran prototypes in staging environments.",
            ]
            initialized = initialize_workspace(workspace, base)
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            resume = sample_resume()
            resume["experience"][0]["bullets"] = [
                "Built backend services with Java.",  # JavaScript must NOT authorize Java
                "Managed relational databases with SQL.",  # MySQL must NOT authorize generic SQL
                "Ran production systems in live environments.",  # prototype must NOT authorize production
            ]
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)
            for i, bullet in enumerate(resume["experience"][0]["bullets"]):
                entry = next(
                    item
                    for item in manifest["entries"]
                    if item["projection_path"] == f"experience[0].bullets[{i}]"
                )
                entry["rendered_text"] = bullet

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("TOOL_DRIFT", codes)
            self.assertIn("UNSUPPORTED_SCOPE", codes)

    def test_cross_entity_metric_transfer_is_blocked_by_path_entity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base = sample_resume()
            base["experience"].append(
                {
                    "company": "Second Corp",
                    "title": "Staff Engineer",
                    "location": "Remote",
                    "dates": "2018 - 2020",
                    "bullets": ["Scaled distributed streaming to 10,000 QPS."],
                }
            )
            initialized = initialize_workspace(workspace, base)
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            # Borrow 10,000 QPS from Second Corp into Example Corp's bullet
            resume = sample_resume()
            resume["experience"].append(base["experience"][1])
            resume["experience"][0]["bullets"][0] = "Implemented a Redis cache serving 10,000 QPS."
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)

            second_entity = next(
                entity
                for entity in initialized["evidence_ledger"]["entities"]
                if "Second Corp" in entity["label"]
            )
            second_claim = second_entity["claims"][0]

            entry = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry["rendered_text"] = resume["experience"][0]["bullets"][0]
            # Try to self-attest Second Corp's entity_id to pass claim-entity check
            entry["entity_id"] = second_entity["entity_id"]
            entry["source_claim_ids"] = [second_claim["claim_id"]]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("PATH_ENTITY_MISMATCH", codes)

    def test_normalization_cannot_introduce_distinct_tool_or_production_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base = sample_resume()
            base["experience"][0]["bullets"] = [
                "Built message queues with RabbitMQ.",
                "Tested prototypes in internal lab.",
            ]
            initialized = initialize_workspace(workspace, base)
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            # Try to normalize RabbitMQ -> Kafka and prototype -> production
            resume = sample_resume()
            resume["experience"][0]["bullets"] = [
                "Built message queues with Kafka.",
                "Deployed production systems in internal lab.",
            ]
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)

            entry_kafka = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry_kafka["rendered_text"] = resume["experience"][0]["bullets"][0]
            entry_kafka["semantic_normalizations"] = [
                {"term": "Kafka", "basis": "Message broker used for event streaming."}
            ]

            entry_prod = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[1]"
            )
            entry_prod["rendered_text"] = resume["experience"][0]["bullets"][1]
            entry_prod["semantic_normalizations"] = [
                {"term": "production", "basis": "Internal lab ran continuously."}
            ]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("TOOL_DRIFT", codes)
            self.assertIn("UNSUPPORTED_SCOPE", codes)

    def test_summary_metric_smuggling_is_blocked_by_path_entity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            # Smuggle 3,000 QPS from experience entity into summary by self-attesting experience entity_id
            resume = sample_resume()
            resume["summary"] = "Backend engineer operating systems at 3,000 QPS."
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)

            exp_entity = next(
                e
                for e in initialized["evidence_ledger"]["entities"]
                if e["entity_type"] == "experience"
            )
            exp_claim = next(c for c in exp_entity["claims"] if "3,000 QPS" in c["claim_text"])

            entry = next(
                item for item in manifest["entries"] if item["projection_path"] == "summary"
            )
            entry["rendered_text"] = resume["summary"]
            entry["entity_id"] = exp_entity["entity_id"]
            entry["source_claim_ids"] = [exp_claim["claim_id"]]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("PATH_ENTITY_MISMATCH", codes)

    def test_distinct_stints_with_same_company_and_title_cannot_share_claims(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base = sample_resume()
            # Stint 1: 2018 - 2020 at Acme
            base["experience"] = [
                {
                    "company": "Acme Corp",
                    "title": "Software Engineer",
                    "location": "Seattle",
                    "dates": "2018 - 2020",
                    "bullets": ["Maintained legacy database systems."],
                },
                # Stint 2: 2022 - Present at Acme (same company and title, different dates)
                {
                    "company": "Acme Corp",
                    "title": "Software Engineer",
                    "location": "Seattle",
                    "dates": "2022 - Present",
                    "bullets": ["Architected distributed storage at 5,000 QPS."],
                },
            ]
            initialized = initialize_workspace(workspace, base)
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            # Try to place the 5,000 QPS metric from Stint 2 into Stint 1's bullet
            resume = sample_resume()
            resume["experience"] = copy.deepcopy(base["experience"])
            resume["experience"][0]["bullets"][0] = (
                "Maintained legacy database systems at 5,000 QPS."
            )
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)

            exp_entities = [
                e
                for e in initialized["evidence_ledger"]["entities"]
                if e["entity_type"] == "experience"
            ]
            stint1_entity = exp_entities[0]
            stint2_entity = exp_entities[1]
            # Verify they have distinct stable entity IDs
            self.assertNotEqual(stint1_entity["entity_id"], stint2_entity["entity_id"])

            stint2_claim = stint2_entity["claims"][0]

            entry = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry["rendered_text"] = resume["experience"][0]["bullets"][0]
            # Try to bind stint 2's claim to stint 1's path
            entry["entity_id"] = stint2_entity["entity_id"]
            entry["source_claim_ids"] = [stint2_claim["claim_id"]]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("PATH_ENTITY_MISMATCH", codes)

    def test_normalization_cannot_introduce_unsupported_dynamic_tool_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base = sample_resume()
            base["experience"][0]["bullets"] = [
                "Built internal messaging with RabbitMQ.",
                "Ran research prototypes in staging.",
            ]
            initialized = initialize_workspace(workspace, base)
            manifest = rebuild_tailoring_manifest(workspace)["manifest"]

            # Try lowercase nats and plural productions
            resume = sample_resume()
            resume["experience"][0]["bullets"] = [
                "Built internal messaging with nats.",
                "Ran research productions in staging.",
            ]
            manifest["resume_fingerprint"] = canonical_json_fingerprint(resume)

            entry_nats = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[0]"
            )
            entry_nats["rendered_text"] = resume["experience"][0]["bullets"][0]
            entry_nats["semantic_normalizations"] = [
                {"term": "nats", "basis": "Lightweight pub-sub broker."}
            ]

            entry_prod = next(
                item
                for item in manifest["entries"]
                if item["projection_path"] == "experience[0].bullets[1]"
            )
            entry_prod["rendered_text"] = resume["experience"][0]["bullets"][1]
            entry_prod["semantic_normalizations"] = [
                {"term": "productions", "basis": "Staging ran like production."}
            ]

            report = audit_resume(resume, manifest, initialized["evidence_ledger"])
            codes = {item["code"] for item in report["findings"]}

            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn("TOOL_DRIFT", codes)
            self.assertIn("UNSUPPORTED_SCOPE", codes)

    def test_dynamic_skills_presentation_binding_passes_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base_resume = sample_resume()
            initialized = initialize_workspace(workspace, base_resume)
            ledger = initialized["evidence_ledger"]

            # Set up experience entity with an Azure OpenAI claim
            exp_entity = next(
                entity for entity in ledger["entities"] if entity["entity_type"] == "experience"
            )
            experience_entity_id = exp_entity["entity_id"]
            azure_claim_id = "claim-exp-azure-openai"
            exp_entity["claims"].append(
                {
                    "claim_id": azure_claim_id,
                    "claim_type": "responsibility",
                    "claim_text": "Built AI diagnostic services on Azure OpenAI.",
                    "evidence_state": "sourced",
                    "status": "active",
                    "provenance": {
                        "source_type": "source_snapshot",
                        "source_fingerprint": initialized["source_snapshot"]["source_fingerprint"],
                        "source_path": "experience[0].bullets[0]",
                        "original_excerpt": "Built AI diagnostic services on Azure OpenAI.",
                    },
                    "tools": ["Azure OpenAI"],
                    "metrics": [],
                    "ownership_level": "implemented",
                    "sourced_at": "2026-01-01T00:00:00Z",
                    "confirmed_at": None,
                    "revoked_at": None,
                    "supersedes": [],
                }
            )

            # Set up skill entity with a RAG claim
            skill_entity = next(
                entity for entity in ledger["entities"] if entity["entity_type"] == "skill"
            )
            skill_entity_id = skill_entity["entity_id"]
            rag_claim_id = "claim-skill-rag"
            skill_entity["claims"].append(
                {
                    "claim_id": rag_claim_id,
                    "claim_type": "responsibility",
                    "claim_text": "Built retrieval systems with RAG architectures.",
                    "evidence_state": "candidate_confirmed",
                    "status": "active",
                    "provenance": {
                        "source_type": "candidate_confirmation",
                        "source_fingerprint": initialized["source_snapshot"]["source_fingerprint"],
                        "source_path": "skills[0].items",
                        "original_excerpt": "RAG",
                    },
                    "tools": ["RAG"],
                    "metrics": [],
                    "ownership_level": "implemented",
                    "sourced_at": "2026-01-01T00:00:00Z",
                    "confirmed_at": "2026-01-01T00:00:00Z",
                    "revoked_at": None,
                    "supersedes": [],
                }
            )

            resume = copy.deepcopy(base_resume)
            resume["skills"] = [
                {
                    "category": "AI Platforms & Tooling",
                    "items": ["Azure OpenAI", "RAG"],
                }
            ]

            rebuilt = rebuild_tailoring_manifest(workspace)
            base_entries = [
                entry
                for entry in rebuilt["manifest"]["entries"]
                if not entry["projection_path"].startswith("skills")
            ]
            skill_entries = [
                {
                    "projection_path": "skills[0].category",
                    "operation": "REWORD",
                    "rendered_text": "AI Platforms & Tooling",
                    "binding_mode": "presentation",
                    "entity_id": None,
                    "source_claim_ids": [],
                    "grouped_item_paths": ["skills[0].items[0]", "skills[0].items[1]"],
                    "match_type": "direct",
                    "semantic_normalizations": [],
                    "reason": "Groups selected AI platform evidence for display.",
                },
                {
                    "projection_path": "skills[0].items[0]",
                    "operation": "LEAD_WITH",
                    "rendered_text": "Azure OpenAI",
                    "binding_mode": "single_entity",
                    "entity_id": experience_entity_id,
                    "source_claim_ids": [azure_claim_id],
                    "match_type": "direct",
                    "semantic_normalizations": [],
                    "reason": "Direct target capability.",
                },
                {
                    "projection_path": "skills[0].items[1]",
                    "operation": "KEEP",
                    "rendered_text": "RAG",
                    "binding_mode": "single_entity",
                    "entity_id": skill_entity_id,
                    "source_claim_ids": [rag_claim_id],
                    "match_type": "direct",
                    "semantic_normalizations": [],
                    "reason": "Used by selected experience evidence.",
                },
            ]
            manifest = {
                "schema_version": 1,
                "target_jd_fingerprint": None,
                "resume_fingerprint": canonical_json_fingerprint(resume),
                "generated_at": "2026-01-01T00:00:00Z",
                "entries": base_entries + skill_entries,
                "removed_entries": [
                    {
                        "source_path": "skills[0].category",
                        "source_text": base_resume["skills"][0]["category"],
                        "entity_id": skill_entity_id,
                        "source_claim_ids": [],
                        "operation": "REMOVE",
                        "reason": "Replaced by presentation category.",
                    },
                    {
                        "source_path": "skills[0].items",
                        "source_text": base_resume["skills"][0]["items"],
                        "entity_id": skill_entity_id,
                        "source_claim_ids": [],
                        "operation": "REMOVE",
                        "reason": "Replaced by itemized presentation items.",
                    },
                ],
                "warning_dispositions": [],
            }

            report = audit_resume(resume, manifest, ledger, base_resume=base_resume)
            self.assertEqual(report["verdict"], "PASS")
            self.assertEqual(report["findings"], [])

    def test_invalid_presentation_binding_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base_resume = sample_resume()
            initialized = initialize_workspace(workspace, base_resume)
            ledger = initialized["evidence_ledger"]
            rebuilt = rebuild_tailoring_manifest(workspace)

            resume = copy.deepcopy(base_resume)
            manifest = rebuilt["manifest"]
            summary_entry = next(
                entry for entry in manifest["entries"] if entry["projection_path"] == "summary"
            )
            summary_entry["binding_mode"] = "presentation"
            summary_entry["grouped_item_paths"] = ["skills[0].items[0]"]

            report = audit_resume(resume, manifest, ledger, base_resume=base_resume)
            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn(
                "INVALID_PRESENTATION_BINDING",
                {finding["code"] for finding in report["findings"]},
            )

    def test_unsupported_presentation_term_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            base_resume = sample_resume()
            initialized = initialize_workspace(workspace, base_resume)
            ledger = initialized["evidence_ledger"]

            exp_entity = next(
                entity for entity in ledger["entities"] if entity["entity_type"] == "experience"
            )
            exp_entity["claims"].append(
                {
                    "claim_id": "claim-exp-azure",
                    "claim_type": "responsibility",
                    "claim_text": "Built services on Azure OpenAI.",
                    "evidence_state": "sourced",
                    "status": "active",
                    "provenance": {
                        "source_type": "source_snapshot",
                        "source_fingerprint": initialized["source_snapshot"]["source_fingerprint"],
                        "source_path": "experience[0].bullets[0]",
                        "original_excerpt": "Built services on Azure OpenAI.",
                    },
                    "tools": ["Azure OpenAI"],
                    "metrics": [],
                    "ownership_level": "implemented",
                    "sourced_at": "2026-01-01T00:00:00Z",
                    "confirmed_at": None,
                    "revoked_at": None,
                    "supersedes": [],
                }
            )

            resume = copy.deepcopy(base_resume)
            resume["skills"] = [
                {
                    "category": "OAuth & AI Platforms",
                    "items": ["Azure OpenAI"],
                }
            ]

            manifest = {
                "schema_version": 1,
                "target_jd_fingerprint": None,
                "resume_fingerprint": canonical_json_fingerprint(resume),
                "generated_at": "2026-01-01T00:00:00Z",
                "entries": [
                    entry
                    for entry in rebuild_tailoring_manifest(workspace)["manifest"]["entries"]
                    if not entry["projection_path"].startswith("skills")
                ]
                + [
                    {
                        "projection_path": "skills[0].category",
                        "operation": "REWORD",
                        "rendered_text": "OAuth & AI Platforms",
                        "binding_mode": "presentation",
                        "entity_id": None,
                        "source_claim_ids": [],
                        "grouped_item_paths": ["skills[0].items[0]"],
                        "match_type": "direct",
                        "semantic_normalizations": [],
                        "reason": "Groups AI platform evidence.",
                    },
                    {
                        "projection_path": "skills[0].items[0]",
                        "operation": "LEAD_WITH",
                        "rendered_text": "Azure OpenAI",
                        "binding_mode": "single_entity",
                        "entity_id": exp_entity["entity_id"],
                        "source_claim_ids": ["claim-exp-azure"],
                        "match_type": "direct",
                        "semantic_normalizations": [],
                        "reason": "Target capability.",
                    },
                ],
                "removed_entries": [],
                "warning_dispositions": [],
            }

            report = audit_resume(resume, manifest, ledger)
            self.assertEqual(report["verdict"], "FAIL")
            self.assertIn(
                "UNSUPPORTED_PRESENTATION_TERM",
                {finding["code"] for finding in report["findings"]},
            )


if __name__ == "__main__":
    unittest.main()
