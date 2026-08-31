#!/usr/bin/env python3
"""Validate and materialize model-produced resume projection artifacts."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.resume_cache_manager import validate_jd_analysis
from scripts.resume_shared import (
    canonical_json_fingerprint,
    entity_anchor,
    load_json_file,
    stable_identifier,
)

CACHE_DIR = "cache"
PLAN_NAME = "projection-plan.json"
LANGUAGE_NAME = "projection-language.json"
WORKING_NAME = "resume-working.json"
MANIFEST_NAME = "resume-changes.json"
LEDGER_NAME = "candidate-evidence.json"
SNAPSHOT_NAME = "base-resume.json"
JD_NAME = "jd-analysis.json"

PlanStatus = Literal["needs_clarification", "ready", "revision_required"]


@dataclass(frozen=True)
class BuildResult:
    status: str
    resume_path: Path | None
    manifest_path: Path | None
    clarifications: tuple[dict[str, Any], ...]


def _workspace_paths(workspace: Path) -> dict[str, Path]:
    cache_dir = workspace / CACHE_DIR
    return {
        "cache": cache_dir,
        "snapshot": cache_dir / SNAPSHOT_NAME,
        "ledger": cache_dir / LEDGER_NAME,
        "working": cache_dir / WORKING_NAME,
        "manifest": cache_dir / MANIFEST_NAME,
        "jd": cache_dir / JD_NAME,
        "plan": cache_dir / PLAN_NAME,
        "language": cache_dir / LANGUAGE_NAME,
    }


def _active_claim_index(ledger: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    """Map active, verified claim IDs to (entity_id, claim)."""
    claim_index: dict[str, tuple[str, dict[str, Any]]] = {}
    for entity in ledger.get("entities", []):
        entity_id = entity.get("entity_id", "")
        for claim in entity.get("claims", []):
            if (
                claim.get("status") == "active"
                and claim.get("evidence_state") in {"sourced", "candidate_confirmed"}
                and claim.get("revoked_at") is None
            ):
                claim_id = claim.get("claim_id")
                if claim_id:
                    claim_index[claim_id] = (entity_id, claim)
    return claim_index


def _capability_index(jd_analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map capability IDs to capability objects."""
    index: dict[str, dict[str, Any]] = {}
    for cap in jd_analysis.get("capabilities", []):
        cap_id = cap.get("capability_id")
        if cap_id:
            index[cap_id] = cap
    return index


def _base_experience_entity_ids(snapshot: dict[str, Any]) -> list[str]:
    """Return entity IDs for all formal experience entries in base resume snapshot."""
    ids: list[str] = []
    for index, _ in enumerate(snapshot.get("experience", [])):
        _, identity = entity_anchor(snapshot, "experience", f"experience[{index}]")
        ids.append(stable_identifier("experience", identity))
    return ids


def _intent_records(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect all content intent records from summary, experience, and optional sections."""
    records: list[dict[str, Any]] = []
    summary_intent = plan.get("summary_intent")
    if isinstance(summary_intent, dict) and summary_intent.get("intent_id"):
        records.append(summary_intent)

    for exp_plan in plan.get("experience_plans", []):
        if isinstance(exp_plan, dict):
            for intent in exp_plan.get("content_intents", []):
                if isinstance(intent, dict):
                    records.append(intent)

    for opt_section in plan.get("optional_sections", []):
        if isinstance(opt_section, dict):
            for intent in opt_section.get("content_intents", []):
                if isinstance(intent, dict):
                    records.append(intent)

    return records


def _validate_constraints(plan: dict[str, Any]) -> None:
    """Validate top-level schema fields and constraints."""
    if not isinstance(plan, dict):
        raise ValueError("Projection Plan must be an object.")

    if plan.get("schema_version") != 1:
        raise ValueError(
            f"Projection Plan schema_version must be 1, got {plan.get('schema_version')}."
        )

    status = plan.get("status")
    if status not in {"needs_clarification", "ready", "revision_required"}:
        raise ValueError(
            f"Projection Plan status must be 'needs_clarification', 'ready', or 'revision_required', got '{status}'."
        )

    revision = plan.get("revision")
    if not isinstance(revision, int) or revision < 1 or revision > 3:
        raise ValueError(
            f"Projection Plan revision must be an integer between 1 and 3, got {revision}."
        )

    constraints = plan.get("constraints")
    if constraints is not None:
        if not isinstance(constraints, dict):
            raise ValueError("Projection Plan constraints must be an object.")
        if constraints.get("page_size") not in (None, "A4"):
            raise ValueError("constraints.page_size must be 'A4'.")
        if constraints.get("page_count") not in (None, 1):
            raise ValueError("constraints.page_count must be 1.")
        if constraints.get("clarification_question_max") not in (None, 5):
            raise ValueError("constraints.clarification_question_max must be 5.")
        if constraints.get("content_fit_revision_max") not in (None, 3):
            raise ValueError("constraints.content_fit_revision_max must be 3.")
        if constraints.get("experience_bullet_min") not in (None, 1):
            raise ValueError("constraints.experience_bullet_min must be 1.")
        if constraints.get("experience_bullet_max") not in (None, 5):
            raise ValueError("constraints.experience_bullet_max must be 5.")
        if constraints.get("skills_group_min") not in (None, 2):
            raise ValueError("constraints.skills_group_min must be 2.")
        if constraints.get("skills_group_max") not in (None, 4):
            raise ValueError("constraints.skills_group_max must be 4.")


def _validate_clarifications(
    plan: dict[str, Any],
    capability_index: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Validate clarification questions."""
    clarifications = plan.get("clarifications", [])
    if not isinstance(clarifications, list):
        raise ValueError("clarifications must be an array.")

    if len(clarifications) > 5:
        raise ValueError(
            f"Maximum 5 clarification questions allowed, got {len(clarifications)}."
        )

    if plan.get("status") == "needs_clarification":
        if len(clarifications) == 0:
            raise ValueError(
                "Projection Plan with status 'needs_clarification' must contain 1-5 clarification questions."
            )

    for index, item in enumerate(clarifications):
        if not isinstance(item, dict):
            raise ValueError(f"clarifications[{index}] must be an object.")
        if not isinstance(item.get("question_id"), str) or not item["question_id"].strip():
            raise ValueError(f"clarifications[{index}].question_id must be a non-empty string.")
        if not isinstance(item.get("question"), str) or not item["question"].strip():
            raise ValueError(f"clarifications[{index}].question must be a non-empty string.")
        cap_ids = item.get("capability_ids")
        if not isinstance(cap_ids, list) or not cap_ids:
            raise ValueError(f"clarifications[{index}].capability_ids must be a non-empty array.")
        for c_idx, cap_id in enumerate(cap_ids):
            if not isinstance(cap_id, str) or not cap_id.strip():
                raise ValueError(
                    f"clarifications[{index}].capability_ids[{c_idx}] must be a non-empty string."
                )
            if capability_index is not None and cap_id not in capability_index:
                raise ValueError(
                    f"Clarification question '{item['question_id']}' references unknown capability_id: {cap_id}."
                )


def _validate_experience_coverage(plan: dict[str, Any], expected_ids: list[str]) -> None:
    """Ensure all formal experience entities from base resume are covered in plan."""
    exp_plans = plan.get("experience_plans")
    if not isinstance(exp_plans, list):
        raise ValueError("experience_plans must be an array.")

    covered_ids: set[str] = set()
    for index, exp_plan in enumerate(exp_plans):
        if not isinstance(exp_plan, dict):
            raise ValueError(f"experience_plans[{index}] must be an object.")

        entity_id = exp_plan.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError(f"experience_plans[{index}].entity_id must be a non-empty string.")

        if entity_id in covered_ids:
            raise ValueError(f"Duplicate experience entity_id in plan: {entity_id}")
        covered_ids.add(entity_id)

        if entity_id not in expected_ids:
            raise ValueError(
                f"Unknown experience entity_id '{entity_id}' not found in Source Snapshot."
            )

        importance = exp_plan.get("importance")
        if importance not in {"critical", "important", "supporting"}:
            raise ValueError(
                f"experience_plans[{index}].importance must be 'critical', 'important', or 'supporting', got '{importance}'."
            )

        target_bullet_count = exp_plan.get("target_bullet_count")
        if (
            not isinstance(target_bullet_count, int)
            or target_bullet_count < 1
            or target_bullet_count > 5
        ):
            raise ValueError(
                f"experience_plans[{index}].target_bullet_count must be an integer between 1 and 5, got {target_bullet_count}."
            )

        reason = exp_plan.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"experience_plans[{index}].reason must be a non-empty string.")

        content_intents = exp_plan.get("content_intents")
        if not isinstance(content_intents, list):
            raise ValueError(f"experience_plans[{index}].content_intents must be an array.")

        if plan.get("status") == "ready" and len(content_intents) != target_bullet_count:
            raise ValueError(
                f"experience_plans[{index}] has target_bullet_count={target_bullet_count} but contains {len(content_intents)} content intents."
            )

    missing = [eid for eid in expected_ids if eid not in covered_ids]
    if missing:
        raise ValueError(
            f"Missing formal experience entity in Projection Plan: {', '.join(missing)}"
        )


def _validate_intents(
    plan: dict[str, Any],
    claim_index: dict[str, tuple[str, dict[str, Any]]],
    capability_index: dict[str, dict[str, Any]],
) -> None:
    """Validate all Content Intent records, ensuring unique IDs and valid evidence/capability links."""
    seen_intent_ids: set[str] = set()

    def validate_intent_record(
        intent: dict[str, Any],
        expected_entity_id: str | None = None,
        context_name: str = "intent",
    ) -> None:
        if not isinstance(intent, dict):
            raise ValueError(f"{context_name} must be an object.")

        intent_id = intent.get("intent_id")
        if not isinstance(intent_id, str) or not intent_id.strip():
            raise ValueError(f"{context_name}.intent_id must be a non-empty string.")

        if intent_id in seen_intent_ids:
            raise ValueError(f"Duplicate intent_id found: {intent_id}")
        seen_intent_ids.add(intent_id)

        claim_ids = intent.get("claim_ids")
        if not isinstance(claim_ids, list) or not claim_ids:
            raise ValueError(f"{context_name} '{intent_id}' must have a non-empty claim_ids array.")

        entity_ids_in_intent: set[str] = set()
        for c_idx, claim_id in enumerate(claim_ids):
            if not isinstance(claim_id, str) or not claim_id.strip():
                raise ValueError(f"{context_name} '{intent_id}'.claim_ids[{c_idx}] must be a string.")
            if claim_id not in claim_index:
                raise ValueError(
                    f"Intent '{intent_id}' references unknown, inactive, or revoked claim_id: {claim_id}"
                )
            entity_id, _ = claim_index[claim_id]
            entity_ids_in_intent.add(entity_id)

        if len(entity_ids_in_intent) > 1:
            raise ValueError(
                f"Content Intent '{intent_id}' combines claims across multiple entities: {', '.join(sorted(entity_ids_in_intent))}"
            )

        if expected_entity_id is not None:
            claim_entity_id = next(iter(entity_ids_in_intent))
            if claim_entity_id != expected_entity_id:
                raise ValueError(
                    f"Content Intent '{intent_id}' claim entity '{claim_entity_id}' does not match experience entity '{expected_entity_id}'."
                )

        cap_ids = intent.get("capability_ids")
        if not isinstance(cap_ids, list):
            raise ValueError(f"{context_name} '{intent_id}'.capability_ids must be an array.")
        for cap_id in cap_ids:
            if not isinstance(cap_id, str) or not cap_id.strip():
                raise ValueError(f"{context_name} '{intent_id}' capability_ids must contain non-empty strings.")
            if cap_id not in capability_index:
                raise ValueError(f"Intent '{intent_id}' references unknown capability_id: {cap_id}")

        content_intent_text = intent.get("content_intent")
        if not isinstance(content_intent_text, str) or not content_intent_text.strip():
            raise ValueError(f"{context_name} '{intent_id}'.content_intent must be a non-empty string.")

        target_lines = intent.get("target_lines")
        if target_lines is not None and (not isinstance(target_lines, int) or target_lines < 1):
            raise ValueError(f"{context_name} '{intent_id}'.target_lines must be a positive integer.")

    summary_intent = plan.get("summary_intent")
    if isinstance(summary_intent, dict) and summary_intent:
        validate_intent_record(summary_intent, expected_entity_id=None, context_name="summary_intent")

    for exp_plan in plan.get("experience_plans", []):
        if isinstance(exp_plan, dict):
            exp_entity_id = exp_plan.get("entity_id")
            for intent in exp_plan.get("content_intents", []):
                validate_intent_record(
                    intent,
                    expected_entity_id=exp_entity_id,
                    context_name=f"experience '{exp_entity_id}' intent",
                )

    for opt_section in plan.get("optional_sections", []):
        if isinstance(opt_section, dict):
            for intent in opt_section.get("content_intents", []):
                validate_intent_record(intent, context_name="optional_section intent")


def _validate_skill_groups(
    plan: dict[str, Any],
    claim_index: dict[str, tuple[str, dict[str, Any]]],
    capability_index: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Validate dynamic Skills Presentation Groups and item-level claim bindings."""
    skills_plan = plan.get("skills_plan")
    if skills_plan is None and plan.get("status") != "ready":
        return

    if not isinstance(skills_plan, dict):
        raise ValueError("skills_plan must be an object.")

    groups = skills_plan.get("groups")
    if not isinstance(groups, list):
        raise ValueError("skills_plan.groups must be an array.")

    if plan.get("status") == "ready":
        if len(groups) < 2 or len(groups) > 4:
            raise ValueError(
                f"Skills plan must contain 2 to 4 Skill Presentation Groups, got {len(groups)}."
            )
    else:
        if len(groups) > 4:
            raise ValueError(
                f"Skills plan cannot contain more than 4 groups, got {len(groups)}."
            )

    for g_idx, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"skills_plan.groups[{g_idx}] must be an object.")

        category = group.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"skills_plan.groups[{g_idx}].category must be a non-empty string.")

        items = group.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"skills_plan.groups[{g_idx}].items must be a non-empty array.")

        for i_idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"skills_plan.groups[{g_idx}].items[{i_idx}] must be an object.")

            display_term = item.get("display_term")
            if not isinstance(display_term, str) or not display_term.strip():
                raise ValueError(
                    f"skills_plan.groups[{g_idx}].items[{i_idx}].display_term must be a non-empty string."
                )

            claim_ids = item.get("claim_ids")
            if not isinstance(claim_ids, list) or not claim_ids:
                raise ValueError(
                    f"Skill item '{display_term}' must have a non-empty claim_ids array."
                )

            for c_idx, claim_id in enumerate(claim_ids):
                if not isinstance(claim_id, str) or not claim_id.strip():
                    raise ValueError(
                        f"Skill item '{display_term}'.claim_ids[{c_idx}] must be a non-empty string."
                    )
                if claim_id not in claim_index:
                    raise ValueError(
                        f"Skill item '{display_term}' references unknown, inactive, or revoked claim_id: {claim_id}"
                    )

            cap_ids = item.get("capability_ids")
            if cap_ids is not None:
                if not isinstance(cap_ids, list):
                    raise ValueError(f"Skill item '{display_term}'.capability_ids must be an array.")
                for cap_id in cap_ids:
                    if not isinstance(cap_id, str) or not cap_id.strip():
                        raise ValueError(
                            f"Skill item '{display_term}' capability_ids must contain non-empty strings."
                        )
                    if capability_index is not None and cap_id not in capability_index:
                        raise ValueError(
                            f"Skill item '{display_term}' references unknown capability_id: {cap_id}"
                        )

            basis = item.get("basis")
            if basis is not None and (not isinstance(basis, str) or not basis.strip()):
                raise ValueError(f"Skill item '{display_term}'.basis must be a non-empty string.")


def validate_projection_plan(workspace: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a model-produced Projection Plan against the workspace JD, Snapshot, and Ledger."""
    paths = _workspace_paths(workspace.resolve())
    if not paths["jd"].exists():
        raise FileNotFoundError(f"JD analysis file not found at {paths['jd']}")
    if not paths["snapshot"].exists():
        raise FileNotFoundError(f"Source snapshot file not found at {paths['snapshot']}")
    if not paths["ledger"].exists():
        raise FileNotFoundError(f"Evidence ledger file not found at {paths['ledger']}")

    jd_analysis = load_json_file(paths["jd"])
    validate_jd_analysis(jd_analysis)
    snapshot = load_json_file(paths["snapshot"])
    ledger = load_json_file(paths["ledger"])

    if plan.get("target_jd_fingerprint") != canonical_json_fingerprint(jd_analysis):
        raise ValueError("Projection Plan has a stale JD fingerprint.")
    source_fingerprint = str(snapshot.get("source_fingerprint", ""))
    if plan.get("source_snapshot_fingerprint") != source_fingerprint:
        raise ValueError("Projection Plan has a stale Source Snapshot fingerprint.")

    capability_index = _capability_index(jd_analysis)
    claim_index = _active_claim_index(ledger)

    _validate_constraints(plan)
    _validate_clarifications(plan, capability_index)
    _validate_experience_coverage(plan, _base_experience_entity_ids(snapshot))
    _validate_intents(plan, claim_index, capability_index)
    _validate_skill_groups(plan, claim_index, capability_index)

    return {
        "status": str(plan["status"]),
        "clarifications": copy.deepcopy(plan.get("clarifications", [])),
        "intent_count": len(_intent_records(plan)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and materialize model-produced resume projection artifacts."
    )
    subparsers = parser.add_subparsers(dest="action", help="Action to execute")

    validate_parser = subparsers.add_parser("validate", help="Validate a projection plan")
    validate_parser.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Path to candidate workspace directory",
    )
    validate_parser.add_argument(
        "--plan",
        type=Path,
        default=None,
        help="Path to projection-plan.json (defaults to workspace/cache/projection-plan.json)",
    )

    args = parser.parse_args()

    if args.action == "validate":
        try:
            workspace = args.workspace.resolve()
            plan_path = args.plan.resolve() if args.plan else workspace / CACHE_DIR / PLAN_NAME
            if not plan_path.exists():
                sys.stderr.write(f"Projection plan file not found: {plan_path}\n")
                return 1

            plan = load_json_file(plan_path)
            result = validate_projection_plan(workspace, plan)
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
            if result["status"] == "needs_clarification":
                return 2
            return 0
        except (FileNotFoundError, OSError, ValueError) as err:
            sys.stderr.write(f"Validation error: {err}\n")
            return 1
        except Exception as err:  # noqa: BLE001
            sys.stderr.write(f"Unexpected error: {err}\n")
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
