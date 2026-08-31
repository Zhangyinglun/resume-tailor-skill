#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manage the candidate Evidence Ledger and its Source Snapshot."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.resume_shared import (  # noqa: E402
    canonical_json_fingerprint,
    entity_anchor,
    iter_resume_text_fields,
    load_json_file,
    slugify_token,
    stable_identifier,
    validate_resume_content,
    write_json_file,
)

CACHE_DIR = Path("cache")
SOURCE_SNAPSHOT_NAME = "base-resume.json"
EVIDENCE_LEDGER_NAME = "candidate-evidence.json"
CANDIDATE_PROFILE_NAME = "candidate-profile.json"
WORKING_RESUME_NAME = "resume-working.json"
TAILORING_MANIFEST_NAME = "resume-changes.json"

_stable_id = stable_identifier
_slug = slugify_token
_entity_anchor = entity_anchor

_TOOL_TERMS = (
    "AWS",
    "Azure",
    "C#",
    "C++",
    "ClickHouse",
    "Docker",
    "FastAPI",
    "GCP",
    "Go",
    "Java",
    "JavaScript",
    "Kafka",
    "Kubernetes",
    "MongoDB",
    "MySQL",
    "NATS",
    "Node.js",
    "OpenAI",
    "Pinecone",
    "PostgreSQL",
    "PyTorch",
    "Python",
    "RAG",
    "RabbitMQ",
    "React",
    "Redis",
    "Rust",
    "Spark",
    "SQL",
    "TensorFlow",
    "Terraform",
    "TypeScript",
    "vLLM",
)
_METRIC_RE = re.compile(
    r"(?<!\w)(?:[$€£¥]\s*)?\d+(?:[.,]\d+)*(?:\s*(?:%|x|×|ms|s|sec(?:onds?)?|"
    r"minutes?|hours?|days?|weeks?|months?|years?|qps|rps|k|m|b|million|billion))?(?!\w)",
    re.IGNORECASE,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_payload(resume: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(resume)
    payload.pop("source_fingerprint", None)
    payload.pop("captured_at", None)
    return payload


_entity_anchor = entity_anchor


def _claim_type(path: str) -> str:
    if ".bullets[" in path:
        return "achievement"
    field = path.rsplit(".", 1)[-1]
    return {
        "items": "technology",
        "tech": "technology",
        "dates": "date",
        "contact": "contact",
        "summary": "summary",
        "title": "role",
    }.get(field, "attribute")


_CASE_SENSITIVE_TOOL_TERMS = {"Go"}


def _extract_tools(text: str) -> list[str]:
    """Extract known tool terms; ambiguous short names such as Go stay case-sensitive."""
    found: list[str] = []
    for term in _TOOL_TERMS:
        flags = re.IGNORECASE if term not in _CASE_SENSITIVE_TOOL_TERMS else 0
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags):
            found.append(term)
    return found


def _extract_metrics(text: str) -> list[dict[str, str]]:
    return [{"value": match.group(0).strip()} for match in _METRIC_RE.finditer(text)]


def _infer_ownership(text: str) -> str:
    lowered = text.casefold()
    if re.search(r"\b(?:led|headed|spearheaded|directed)\b", lowered):
        return "led"
    if re.search(r"\b(?:owned|architected|oversaw)\b", lowered):
        return "owned"
    if re.search(r"\b(?:implemented|built|developed|designed|created|engineered)\b", lowered):
        return "implemented"
    return "contributed"


def _build_source_entities(resume: dict[str, Any], source_fingerprint: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    captured_at = _now()
    for path, text, entity_type, entity_key in iter_resume_text_fields(resume):
        label, identity = _entity_anchor(resume, entity_type, entity_key)
        entity_id = _stable_id(entity_type, identity)
        entity = grouped.setdefault(
            entity_id,
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "label": label,
                "state": "active",
                "claims": [],
            },
        )
        claim_type = _claim_type(path)
        claim_id = _stable_id("claim", entity_id, claim_type, text)
        if any(claim["claim_id"] == claim_id for claim in entity["claims"]):
            continue
        entity["claims"].append(
            {
                "claim_id": claim_id,
                "claim_type": claim_type,
                "claim_text": text,
                "evidence_state": "sourced",
                "status": "active",
                "provenance": {
                    "source_type": "source_snapshot",
                    "source_fingerprint": source_fingerprint,
                    "source_path": path,
                    "original_excerpt": text,
                },
                "tools": _extract_tools(text),
                "metrics": _extract_metrics(text),
                "ownership_level": _infer_ownership(text),
                "sourced_at": captured_at,
                "confirmed_at": None,
                "revoked_at": None,
                "supersedes": [],
            }
        )
    return list(grouped.values())


def _candidate_id(resume: dict[str, Any]) -> str:
    return _stable_id("candidate", str(resume.get("name", "candidate")).strip())


def _paths(workspace: Path) -> dict[str, Path]:
    cache = workspace / CACHE_DIR
    return {
        "snapshot": cache / SOURCE_SNAPSHOT_NAME,
        "ledger": cache / EVIDENCE_LEDGER_NAME,
        "profile": cache / CANDIDATE_PROFILE_NAME,
        "working": cache / WORKING_RESUME_NAME,
        "manifest": cache / TAILORING_MANIFEST_NAME,
    }


def initialize_workspace(workspace: Path, resume: dict[str, Any]) -> dict[str, Any]:
    """Initialize a candidate workspace from one validated source resume."""
    validate_resume_content(resume, require_non_empty=True)
    paths = _paths(workspace)
    existing = [
        path
        for key, path in paths.items()
        if key in {"snapshot", "ledger", "profile"} and path.exists()
    ]
    if existing:
        raise ValueError(
            "Candidate workspace is already initialized; use sync for a new source resume."
        )

    source = _source_payload(resume)
    source_fingerprint = canonical_json_fingerprint(source)
    snapshot = copy.deepcopy(source)
    snapshot["source_fingerprint"] = source_fingerprint
    snapshot["captured_at"] = _now()
    ledger = {
        "schema_version": 1,
        "candidate_id": _candidate_id(source),
        "base_source_fingerprint": source_fingerprint,
        "updated_at": _now(),
        "entities": _build_source_entities(source, source_fingerprint),
    }
    profile = {
        "schema_version": 1,
        "candidate_id": ledger["candidate_id"],
        "updated_at": _now(),
        "target_direction": "",
        "preferences": {},
    }

    write_json_file(paths["snapshot"], snapshot)
    write_json_file(paths["ledger"], ledger)
    write_json_file(paths["profile"], profile)
    write_json_file(paths["working"], source)
    return {
        "status": "initialized",
        "source_snapshot": snapshot,
        "evidence_ledger": ledger,
        "candidate_profile": profile,
    }


def _deep_merge(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(target)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def ingest_candidate_response(workspace: Path, response: dict[str, Any]) -> dict[str, Any]:
    """Silently ingest candidate-confirmed claims and presentation preferences."""
    paths = _paths(workspace)
    ledger = load_json_file(paths["ledger"])
    profile = load_json_file(paths["profile"])
    claims_input = response.get("claims", [])
    preferences = response.get("preferences", {})
    if not isinstance(claims_input, list):
        raise ValueError("`claims` must be an array.")
    if not isinstance(preferences, dict):
        raise ValueError("`preferences` must be an object.")

    entities = {
        str(entity.get("entity_id")): entity
        for entity in ledger.get("entities", [])
        if isinstance(entity, dict)
    }
    claim_index = {
        str(claim.get("claim_id")): claim
        for entity in entities.values()
        for claim in entity.get("claims", [])
        if isinstance(claim, dict)
    }
    ingested: list[str] = []
    for index, raw_claim in enumerate(claims_input):
        if not isinstance(raw_claim, dict):
            raise ValueError(f"claims[{index}] must be an object.")
        entity_id = str(raw_claim.get("entity_id", "")).strip()
        claim_type = str(raw_claim.get("claim_type", "")).strip()
        claim_text = str(raw_claim.get("claim_text", "")).strip()
        original_excerpt = str(raw_claim.get("original_excerpt", "")).strip()
        if entity_id not in entities:
            raise ValueError(f"claims[{index}] references unknown entity: {entity_id}")
        if not claim_type or not claim_text or not original_excerpt:
            raise ValueError(
                f"claims[{index}] requires claim_type, claim_text, and original_excerpt."
            )
        supersedes = raw_claim.get("supersedes", [])
        if not isinstance(supersedes, list):
            raise ValueError(f"claims[{index}].supersedes must be an array.")
        for superseded_id in supersedes:
            old_claim = claim_index.get(str(superseded_id))
            if old_claim is None:
                raise ValueError(f"claims[{index}] supersedes unknown claim: {superseded_id}")
            if old_claim not in entities[entity_id].get("claims", []):
                raise ValueError(f"claims[{index}] cannot supersede a claim from another entity.")

        claim_id = _stable_id("claim", entity_id, claim_type, claim_text)
        metrics = raw_claim.get("metrics", _extract_metrics(claim_text))
        tools = raw_claim.get("tools", _extract_tools(claim_text))
        if not isinstance(metrics, list) or not isinstance(tools, list):
            raise ValueError(f"claims[{index}] tools and metrics must be arrays.")
        claim = {
            "claim_id": claim_id,
            "claim_type": claim_type,
            "claim_text": claim_text,
            "evidence_state": "candidate_confirmed",
            "status": "active",
            "provenance": {
                "source_type": "candidate_response",
                "source_fingerprint": None,
                "source_path": None,
                "original_excerpt": original_excerpt,
            },
            "tools": [str(tool) for tool in tools],
            "metrics": copy.deepcopy(metrics),
            "ownership_level": str(raw_claim.get("ownership_level", _infer_ownership(claim_text))),
            "confirmed_at": _now(),
            "revoked_at": None,
            "supersedes": [str(item) for item in supersedes],
        }
        entity_claims = entities[entity_id].setdefault("claims", [])
        existing_claim = next(
            (item for item in entity_claims if item.get("claim_id") == claim_id),
            None,
        )
        if existing_claim is None:
            entity_claims.append(claim)
        else:
            # Same (entity, type, text) already exists: promote it in place
            # without discarding source provenance, and merge supersede links.
            if existing_claim.get("evidence_state") != "candidate_confirmed":
                existing_claim["evidence_state"] = "candidate_confirmed"
                existing_claim["confirmed_at"] = _now()
            existing_claim["provenance"]["original_excerpt"] = original_excerpt
            existing_claim["supersedes"] = sorted(
                set(existing_claim.get("supersedes", [])) | {str(item) for item in supersedes}
            )
            existing_claim["tools"] = sorted(
                set(existing_claim.get("tools", [])) | {str(tool) for tool in tools}
            )
            existing_metrics = list(existing_claim.get("metrics", []))
            for metric in metrics:
                if metric not in existing_metrics:
                    existing_metrics.append(metric)
            existing_claim["metrics"] = existing_metrics
            requested_ownership = str(raw_claim.get("ownership_level", "")).strip()
            if requested_ownership:
                existing_claim["ownership_level"] = requested_ownership
            claim = existing_claim
        claim_index[claim_id] = claim
        for superseded_id in supersedes:
            old_claim = claim_index[str(superseded_id)]
            old_claim["status"] = "superseded"
            old_claim["revoked_at"] = _now()
        ingested.append(claim_id)

    profile["preferences"] = _deep_merge(profile.get("preferences", {}), preferences)
    profile["updated_at"] = _now()
    ledger["updated_at"] = _now()
    write_json_file(paths["ledger"], ledger)
    write_json_file(paths["profile"], profile)
    return {
        "status": "ingested",
        "ingested_claim_ids": ingested,
        "evidence_ledger": ledger,
        "candidate_profile": profile,
    }


def rebuild_tailoring_manifest(workspace: Path) -> dict[str, Any]:
    """Rebuild exact claim links for a working projection without inventing evidence."""
    paths = _paths(workspace)
    resume = load_json_file(paths["working"])
    validate_resume_content(resume, require_non_empty=True)
    ledger = load_json_file(paths["ledger"])
    base = _source_payload(load_json_file(paths["snapshot"]))

    active_claims: list[tuple[str, dict[str, Any]]] = []
    for entity in ledger.get("entities", []):
        if entity.get("state") != "active":
            continue
        entity_id = str(entity.get("entity_id", ""))
        for claim in entity.get("claims", []):
            if claim.get("status") == "active" and claim.get("evidence_state") in {
                "sourced",
                "candidate_confirmed",
            }:
                active_claims.append((entity_id, claim))

    base_fields = {path: text for path, text, _, _ in iter_resume_text_fields(base)}
    base_texts = set(base_fields.values())
    working_fields = list(iter_resume_text_fields(resume))
    entries: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for path, text, entity_type, entity_key in working_fields:
        matches = [
            (entity_id, claim)
            for entity_id, claim in active_claims
            if str(claim.get("claim_text", "")).strip() == text.strip()
        ]
        if matches:
            expected_entity_id = _stable_id(
                entity_type, _entity_anchor(resume, entity_type, entity_key)[1]
            )
            same_entity_matches = [match for match in matches if match[0] == expected_entity_id]
            source_path_matches = [
                match
                for match in matches
                if match[1].get("provenance", {}).get("source_path") == path
            ]
            entity_id, claim = (same_entity_matches or source_path_matches or matches)[0]
            claim_ids = [str(claim["claim_id"])]
        else:
            entity_id, claim_ids = None, []
            unresolved.append(path)
        if base_fields.get(path) == text:
            operation = "KEEP"
        elif text in base_texts:
            operation = "REORDER"
        else:
            operation = "REWORD"
        entries.append(
            {
                "projection_path": path,
                "operation": operation,
                "rendered_text": text,
                "entity_id": entity_id,
                "source_claim_ids": claim_ids,
                "match_type": "direct",
                "semantic_normalizations": [],
                "reason": (
                    "Exact active claim match."
                    if claim_ids
                    else "Unresolved manual edit; candidate evidence is required."
                ),
            }
        )

    working_pairs = {(path, text) for path, text, _, _ in working_fields}
    removed_entries: list[dict[str, Any]] = []
    for path, text in base_fields.items():
        if (path, text) in working_pairs:
            continue
        source_claims = [
            (entity_id, claim)
            for entity_id, claim in active_claims
            if claim.get("provenance", {}).get("source_path") == path
            and claim.get("claim_text") == text
        ]
        removed_entries.append(
            {
                "source_path": path,
                "source_text": text,
                "entity_id": source_claims[0][0] if source_claims else None,
                "source_claim_ids": (
                    [str(source_claims[0][1]["claim_id"])] if source_claims else []
                ),
                "operation": "REMOVE",
                "reason": "Source field is absent or changed in the current projection.",
            }
        )

    jd_path = workspace / CACHE_DIR / "jd-analysis.json"
    jd_fingerprint = (
        canonical_json_fingerprint(load_json_file(jd_path)) if jd_path.exists() else None
    )
    manifest = {
        "schema_version": 1,
        "target_jd_fingerprint": jd_fingerprint,
        "resume_fingerprint": canonical_json_fingerprint(resume),
        "generated_at": _now(),
        "entries": entries,
        "removed_entries": removed_entries,
        "warning_dispositions": [],
    }
    write_json_file(paths["manifest"], manifest)
    return {
        "status": "rebuilt",
        "unresolved_paths": unresolved,
        "manifest": manifest,
    }


def revoke_claim(workspace: Path, claim_id: str, reason: str) -> dict[str, Any]:
    """Revoke one claim without deleting its history."""
    if not reason.strip():
        raise ValueError("Claim revocation requires a non-empty reason.")
    paths = _paths(workspace)
    ledger = load_json_file(paths["ledger"])
    for entity in ledger.get("entities", []):
        for claim in entity.get("claims", []):
            if claim.get("claim_id") == claim_id:
                claim["status"] = "revoked"
                claim["revoked_at"] = _now()
                claim["revocation_reason"] = reason.strip()
                ledger["updated_at"] = _now()
                write_json_file(paths["ledger"], ledger)
                return {"status": "revoked", "evidence_ledger": ledger}
    raise ValueError(f"Unknown claim: {claim_id}")


def synchronize_source(workspace: Path, resume: dict[str, Any]) -> dict[str, Any]:
    """Synchronize a changed source while retaining candidate-confirmed history."""
    validate_resume_content(resume, require_non_empty=True)
    paths = _paths(workspace)
    old_snapshot = load_json_file(paths["snapshot"])
    ledger = load_json_file(paths["ledger"])
    profile = load_json_file(paths["profile"])
    source = _source_payload(resume)
    if _candidate_id(source) != ledger.get("candidate_id"):
        raise ValueError("Source candidate does not match this workspace candidate.")
    source_fingerprint = canonical_json_fingerprint(source)
    if source_fingerprint == ledger.get("base_source_fingerprint"):
        return {
            "status": "unchanged",
            "source_snapshot": old_snapshot,
            "evidence_ledger": ledger,
            "candidate_profile": profile,
        }

    generated = {
        entity["entity_id"]: entity for entity in _build_source_entities(source, source_fingerprint)
    }
    existing = {
        entity["entity_id"]: entity
        for entity in ledger.get("entities", [])
        if isinstance(entity, dict) and entity.get("entity_id")
    }
    merged_entities: list[dict[str, Any]] = []
    for entity_id, old_entity in existing.items():
        new_entity = generated.pop(entity_id, None)
        confirmed = [
            copy.deepcopy(claim)
            for claim in old_entity.get("claims", [])
            if claim.get("evidence_state") == "candidate_confirmed"
        ]
        if new_entity is None:
            archived = copy.deepcopy(old_entity)
            archived["state"] = "archived"
            for claim in archived.get("claims", []):
                if claim.get("evidence_state") == "sourced" and claim.get("status") == "active":
                    claim["status"] = "archived"
            merged_entities.append(archived)
            continue

        new_claim_ids = {str(claim["claim_id"]) for claim in new_entity.get("claims", [])}
        confirmed_by_id: dict[str, dict[str, Any]] = {}
        for claim in confirmed:
            confirmed_by_id.setdefault(str(claim.get("claim_id")), claim)
        # Promote regenerated source claims the candidate already confirmed so
        # the ledger never carries duplicate claim IDs.
        for claim in new_entity.get("claims", []):
            confirmed_claim = confirmed_by_id.get(str(claim.get("claim_id")))
            if confirmed_claim is None:
                continue
            claim["evidence_state"] = "candidate_confirmed"
            claim["confirmed_at"] = confirmed_claim.get("confirmed_at") or claim.get("confirmed_at")
            confirmed_excerpt = confirmed_claim.get("provenance", {}).get("original_excerpt")
            if confirmed_excerpt:
                claim["provenance"]["original_excerpt"] = confirmed_excerpt
            claim["ownership_level"] = confirmed_claim.get(
                "ownership_level", claim.get("ownership_level")
            )
            claim["tools"] = sorted(
                set(claim.get("tools", [])) | set(confirmed_claim.get("tools", []))
            )
            kept_metrics = list(claim.get("metrics", []))
            for metric in confirmed_claim.get("metrics", []):
                if metric not in kept_metrics:
                    kept_metrics.append(metric)
            claim["metrics"] = kept_metrics

        kept_ids = set(new_claim_ids)
        extra_confirmed = [
            claim for claim_id, claim in confirmed_by_id.items() if claim_id not in kept_ids
        ]
        kept_ids.update(str(claim.get("claim_id")) for claim in extra_confirmed)
        archived_source = []
        for claim in old_entity.get("claims", []):
            if (
                claim.get("evidence_state") == "sourced"
                and str(claim.get("claim_id")) not in new_claim_ids
                and str(claim.get("claim_id")) not in kept_ids
            ):
                archived_claim = copy.deepcopy(claim)
                archived_claim["status"] = "archived"
                archived_source.append(archived_claim)
                kept_ids.add(str(claim.get("claim_id")))
        new_entity["claims"].extend(extra_confirmed + archived_source)
        merged_entities.append(new_entity)
    merged_entities.extend(generated.values())

    snapshot = copy.deepcopy(source)
    snapshot["source_fingerprint"] = source_fingerprint
    snapshot["captured_at"] = _now()
    ledger["base_source_fingerprint"] = source_fingerprint
    ledger["updated_at"] = _now()
    ledger["entities"] = merged_entities
    write_json_file(paths["snapshot"], snapshot)
    write_json_file(paths["ledger"], ledger)
    write_json_file(paths["working"], source)
    if paths["manifest"].exists():
        paths["manifest"].unlink()
    return {
        "status": "synchronized",
        "source_snapshot": snapshot,
        "evidence_ledger": ledger,
        "candidate_profile": profile,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the candidate Evidence Ledger.")
    parser.add_argument(
        "action",
        choices=("init", "sync", "ingest", "manifest-rebuild", "revoke", "show", "profile-show"),
    )
    parser.add_argument("--workspace", required=True, help="Candidate workspace root")
    parser.add_argument("--source-json", help="Validated source resume JSON for init/sync")
    parser.add_argument("--response-json", help="Candidate response JSON for ingest")
    parser.add_argument("--claim-id", help="Claim ID for revoke")
    parser.add_argument("--reason", help="Reason for revoke")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workspace = Path(args.workspace).expanduser().resolve()
    if workspace == PROJECT_ROOT or PROJECT_ROOT in workspace.parents:
        print(
            "Error: Candidate data must use a workspace outside the Skill package.", file=sys.stderr
        )
        return 1
    try:
        if args.action in {"init", "sync"}:
            if not args.source_json:
                raise ValueError(f"{args.action} requires --source-json.")
            resume = load_json_file(Path(args.source_json).expanduser().resolve())
            result = (
                initialize_workspace(workspace, resume)
                if args.action == "init"
                else synchronize_source(workspace, resume)
            )
        elif args.action == "ingest":
            if not args.response_json:
                raise ValueError("ingest requires --response-json.")
            result = ingest_candidate_response(
                workspace,
                load_json_file(Path(args.response_json).expanduser().resolve()),
            )
        elif args.action == "manifest-rebuild":
            result = rebuild_tailoring_manifest(workspace)
        elif args.action == "revoke":
            if not args.claim_id or not args.reason:
                raise ValueError("revoke requires --claim-id and --reason.")
            result = revoke_claim(workspace, args.claim_id, args.reason)
        elif args.action == "show":
            result = load_json_file(_paths(workspace)["ledger"])
        else:
            result = load_json_file(_paths(workspace)["profile"])
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
