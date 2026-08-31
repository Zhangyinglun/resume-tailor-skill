from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.audit_factual_integrity import audit_resume
from scripts.evidence_ledger_manager import (
    _extract_tools,
    ingest_candidate_response,
    initialize_workspace,
    rebuild_tailoring_manifest,
    revoke_claim,
    synchronize_source,
)


def sample_resume() -> dict[str, Any]:
    return {
        "name": "Alex Chen",
        "contact": "alex@example.com | +1 206-555-0100",
        "summary": "Backend engineer building retrieval systems.",
        "skills": [{"category": "Languages", "items": "Python, Go"}],
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Engineer",
                "location": "Seattle",
                "dates": "2020 - Present",
                "bullets": ["Implemented a Redis cache for document retrieval."],
            }
        ],
        "projects": [],
        "education": [
            {"school": "Example University", "degree": "B.S. Computer Science", "dates": "2020"}
        ],
        "certifications": [],
        "awards": [],
    }


class EvidenceLedgerTests(unittest.TestCase):
    def test_initialize_creates_snapshot_ledger_profile_and_working_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = initialize_workspace(workspace, sample_resume())

            self.assertEqual(result["status"], "initialized")
            snapshot = result["source_snapshot"]
            ledger = result["evidence_ledger"]
            self.assertTrue(snapshot["source_fingerprint"].startswith("sha256:"))
            self.assertEqual(ledger["base_source_fingerprint"], snapshot["source_fingerprint"])
            self.assertTrue(ledger["entities"])
            claims = [claim for entity in ledger["entities"] for claim in entity["claims"]]
            self.assertTrue(all(claim["evidence_state"] == "sourced" for claim in claims))
            self.assertTrue(all(claim["provenance"]["source_path"] for claim in claims))
            self.assertTrue((workspace / "cache" / "base-resume.json").exists())
            self.assertTrue((workspace / "cache" / "candidate-evidence.json").exists())
            self.assertTrue((workspace / "cache" / "candidate-profile.json").exists())
            self.assertTrue((workspace / "cache" / "resume-working.json").exists())

    def test_sync_preserves_confirmed_claims_and_archives_removed_source_entities(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            experience = next(
                entity
                for entity in initialized["evidence_ledger"]["entities"]
                if entity["entity_type"] == "experience"
            )
            ingest_candidate_response(
                workspace,
                {
                    "claims": [
                        {
                            "entity_id": experience["entity_id"],
                            "claim_type": "metric",
                            "claim_text": "The cache sustained 3,000 QPS.",
                            "original_excerpt": "大概能扛住 3000 QPS",
                            "metrics": [{"value": "3,000 QPS"}],
                        }
                    ],
                    "preferences": {"emphasize": ["distributed systems"]},
                },
            )
            updated = sample_resume()
            updated["experience"] = [
                {
                    "company": "New Corp",
                    "title": "Senior Engineer",
                    "location": "Remote",
                    "dates": "2024 - Present",
                    "bullets": ["Built a Python service."],
                }
            ]
            updated["projects"] = [
                {
                    "name": "Retrieval Engine",
                    "tech": "Python",
                    "dates": "2024",
                    "bullets": ["Built a local retrieval prototype."],
                }
            ]

            result = synchronize_source(workspace, updated)
            archived = next(
                entity
                for entity in result["evidence_ledger"]["entities"]
                if entity["entity_id"] == experience["entity_id"]
            )
            confirmed = next(
                claim
                for claim in archived["claims"]
                if claim["evidence_state"] == "candidate_confirmed"
            )
            self.assertEqual(archived["state"], "archived")
            self.assertEqual(confirmed["status"], "active")
            self.assertEqual(
                result["candidate_profile"]["preferences"]["emphasize"], ["distributed systems"]
            )
            self.assertTrue(
                any(
                    entity["entity_type"] == "project"
                    for entity in result["evidence_ledger"]["entities"]
                )
            )

    def test_revoke_claim_retains_history_and_requires_a_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            claim_id = initialized["evidence_ledger"]["entities"][0]["claims"][0]["claim_id"]

            with self.assertRaisesRegex(ValueError, "reason"):
                revoke_claim(workspace, claim_id, "")

            result = revoke_claim(workspace, claim_id, "Candidate corrected the source detail.")
            claim = next(
                claim
                for entity in result["evidence_ledger"]["entities"]
                for claim in entity["claims"]
                if claim["claim_id"] == claim_id
            )
            self.assertEqual(claim["status"], "revoked")
            self.assertIsNotNone(claim["revoked_at"])
            self.assertEqual(claim["revocation_reason"], "Candidate corrected the source detail.")

    def test_manifest_rebuild_links_exact_claims_and_exposes_unresolved_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialize_workspace(workspace, sample_resume())

            exact = rebuild_tailoring_manifest(workspace)
            self.assertEqual(exact["unresolved_paths"], [])
            self.assertTrue(exact["manifest"]["entries"])
            self.assertTrue(
                all(entry["source_claim_ids"] for entry in exact["manifest"]["entries"])
            )

            working_path = workspace / "cache" / "resume-working.json"
            working = sample_resume()
            working["summary"] = "Unconfirmed production architect."
            working_path.write_text(json.dumps(working), encoding="utf-8")
            rebuilt = rebuild_tailoring_manifest(workspace)
            self.assertIn("summary", rebuilt["unresolved_paths"])
            summary_entry = next(
                entry
                for entry in rebuilt["manifest"]["entries"]
                if entry["projection_path"] == "summary"
            )
            self.assertEqual(summary_entry["source_claim_ids"], [])

    def test_sync_promotes_confirmed_claim_without_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            experience = next(
                entity
                for entity in initialized["evidence_ledger"]["entities"]
                if entity["entity_type"] == "experience"
            )
            claim_text = "Implemented a Redis cache for document retrieval."
            ingest_candidate_response(
                workspace,
                {
                    "claims": [
                        {
                            "entity_id": experience["entity_id"],
                            "claim_type": "achievement",
                            "claim_text": claim_text,
                            "original_excerpt": "缓存用于文档检索",
                            "tools": ["Redis"],
                        }
                    ],
                    "preferences": {},
                },
            )
            updated = sample_resume()
            updated["summary"] = "Backend engineer specializing in caching and retrieval."

            result = synchronize_source(workspace, updated)
            claims = [
                claim
                for entity in result["evidence_ledger"]["entities"]
                for claim in entity["claims"]
            ]
            ids = [claim["claim_id"] for claim in claims]
            self.assertEqual(len(ids), len(set(ids)))
            promoted = next(claim for claim in claims if claim["claim_text"] == claim_text)
            self.assertEqual(promoted["evidence_state"], "candidate_confirmed")

            rebuilt = rebuild_tailoring_manifest(workspace)
            report = audit_resume(
                updated,
                rebuilt["manifest"],
                result["evidence_ledger"],
                base_resume=result["source_snapshot"],
            )
            self.assertEqual(report["verdict"], "PASS")

    def test_reingesting_identical_confirmation_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            experience = next(
                entity
                for entity in initialized["evidence_ledger"]["entities"]
                if entity["entity_type"] == "experience"
            )
            response = {
                "claims": [
                    {
                        "entity_id": experience["entity_id"],
                        "claim_type": "metric",
                        "claim_text": "Handled 5,000 requests per second at peak.",
                        "original_excerpt": "峰值 5000 QPS",
                        "metrics": [{"value": "5,000 requests per second"}],
                    }
                ],
                "preferences": {},
            }
            first = ingest_candidate_response(workspace, response)
            second = ingest_candidate_response(workspace, response)
            claim_id = first["ingested_claim_ids"][0]
            first_claim = next(
                claim
                for entity in first["evidence_ledger"]["entities"]
                for claim in entity["claims"]
                if claim["claim_id"] == claim_id
            )
            claims = [
                claim
                for entity in second["evidence_ledger"]["entities"]
                for claim in entity["claims"]
                if claim["claim_id"] == claim_id
            ]
            self.assertEqual(len(claims), 1)
            self.assertEqual(claims[0]["confirmed_at"], first_claim["confirmed_at"])

    def test_extract_tools_does_not_treat_english_go_as_language(self) -> None:
        self.assertNotIn("Go", _extract_tools("Created a go-to-market brief for Python services."))
        self.assertIn("Go", _extract_tools("Built services in Go with Python."))

    def test_source_extraction_deduplicates_identical_bullets_and_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            resume = sample_resume()
            # Repeated identical bullets in same experience entity
            resume["experience"][0]["bullets"] = [
                "Built distributed APIs using Python.",
                "Built distributed APIs using Python.",
            ]
            # Multiple skill categories with same name and content
            resume["skills"] = [
                {"category": "Core", "items": "Python, Go"},
                {"category": "Core", "items": "Python, Go"},
            ]
            initialized = initialize_workspace(workspace, resume)
            ledger = initialized["evidence_ledger"]

            # Verify all claim IDs in each entity are strictly unique
            for entity in ledger["entities"]:
                claim_ids = [c["claim_id"] for c in entity["claims"]]
                self.assertEqual(len(claim_ids), len(set(claim_ids)))

            rebuilt = rebuild_tailoring_manifest(workspace)
            report = audit_resume(
                resume, rebuilt["manifest"], ledger, base_resume=initialized["source_snapshot"]
            )
            self.assertEqual(report["verdict"], "PASS")

    def test_sync_allows_contact_updates_for_same_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialize_workspace(workspace, sample_resume())

            updated = sample_resume()
            # Updated phone, email, and location
            updated["contact"] = (
                "San Francisco, CA | +1 415-555-9999 | alex.new@example.com | linkedin.com/in/alexchen"
            )

            result = synchronize_source(workspace, updated)
            self.assertEqual(result["status"], "synchronized")
            self.assertEqual(result["source_snapshot"]["contact"], updated["contact"])

    def test_sync_preserves_candidate_confirmed_provenance_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            initialized = initialize_workspace(workspace, sample_resume())
            experience = next(
                entity
                for entity in initialized["evidence_ledger"]["entities"]
                if entity["entity_type"] == "experience"
            )
            claim_text = "Implemented a Redis cache for document retrieval."
            ingest_candidate_response(
                workspace,
                {
                    "claims": [
                        {
                            "entity_id": experience["entity_id"],
                            "claim_type": "achievement",
                            "claim_text": claim_text,
                            "original_excerpt": "这是候选人亲自确认的原话摘录",
                            "tools": ["Redis"],
                        }
                    ],
                    "preferences": {},
                },
            )

            updated = sample_resume()
            updated["summary"] = "Senior backend engineer."
            result = synchronize_source(workspace, updated)

            claims = [c for e in result["evidence_ledger"]["entities"] for c in e["claims"]]
            promoted = next(c for c in claims if c["claim_text"] == claim_text)
            self.assertEqual(
                promoted["provenance"]["original_excerpt"], "这是候选人亲自确认的原话摘录"
            )


if __name__ == "__main__":
    unittest.main()
