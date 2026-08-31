#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically audit a Tailored Resume against candidate evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
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
    stable_identifier,
    validate_resume_content,
)

_ALLOWED_EVIDENCE_STATES = {"sourced", "candidate_confirmed"}
_ALLOWED_OPERATIONS = {
    "KEEP",
    "LEAD_WITH",
    "EMPHASIZE",
    "QUANTIFY",
    "DOWNPLAY",
    "MERGE",
    "REWORD",
    "REMOVE",
    "REORDER",
}
_KNOWN_TECH_TERMS = {
    "aws",
    "azure",
    "c#",
    "c++",
    "clickhouse",
    "docker",
    "fastapi",
    "gcp",
    "go",
    "java",
    "javascript",
    "js",
    "kafka",
    "kubernetes",
    "mongodb",
    "mysql",
    "nats",
    "node.js",
    "nosql",
    "openai",
    "pinecone",
    "postgresql",
    "pytorch",
    "python",
    "rag",
    "rabbitmq",
    "react",
    "redis",
    "rust",
    "spark",
    "sql",
    "tensorflow",
    "terraform",
    "typescript",
    "vllm",
}
_SCOPE_TERMS = {
    "production",
    "productions",
    "prototype",
    "prototypes",
    "pilot",
    "pilots",
    "enterprise",
    "global",
}
# Only approved abstract industry concepts (such as RAG) may be introduced via
# self-attested normalization without a direct tool or scope claim.
_NORMALIZABLE_CONCEPTS = {"rag"}
# Short common English words mapped to their exact required casing.
_CASE_SENSITIVE_TERMS = {"go": "Go"}
_METRIC_RE = re.compile(
    r"(?<!\w)(?:[$€£¥]\s*)?\d+(?:[.,]\d+)*(?:\s*(?:%|x|×|ms|s|sec(?:onds?)?|"
    r"minutes?|hours?|days?|weeks?|months?|years?|qps|rps|k|m|b|million|billion))?(?!\w)",
    re.IGNORECASE,
)
_OWNERSHIP_TERMS: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (re.compile(r"\b(?:led|headed|spearheaded|directed)\b", re.IGNORECASE), 3, "led"),
    (re.compile(r"\b(?:owned|architected|oversaw)\b", re.IGNORECASE), 2, "owned"),
    (
        re.compile(
            r"\b(?:implemented|built|developed|designed|created|engineered)\b", re.IGNORECASE
        ),
        1,
        "implemented",
    ),
)
_OWNERSHIP_RANK = {"contributed": 0, "assisted": 0, "implemented": 1, "owned": 2, "led": 3}


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "ERROR", "path": path, "message": message}


def _normalize_metric(value: str) -> str:
    return re.sub(r"[\s,]+", "", value.casefold())


def _metrics(text: str) -> set[str]:
    return {_normalize_metric(match.group(0)) for match in _METRIC_RE.finditer(text)}


def _mentioned_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for term in _KNOWN_TECH_TERMS | _SCOPE_TERMS:
        lookup_pattern = _CASE_SENSITIVE_TERMS.get(term, term)
        flags = 0 if term in _CASE_SENSITIVE_TERMS else re.IGNORECASE
        if re.search(rf"(?<!\w){re.escape(lookup_pattern)}(?!\w)", text, flags):
            terms.add(term.casefold())
    for match in re.finditer(r"(?<!\w)[A-Za-z][A-Za-z0-9+#.-]*(?!\w)", text):
        token = match.group(0).strip(".,;:")
        letters = "".join(character for character in token if character.isalpha())
        has_internal_uppercase = any(character.isupper() for character in token[1:])
        has_technical_punctuation = any(marker in token for marker in ("+", "#", "."))
        if len(letters) >= 2 and (
            letters.isupper() or has_internal_uppercase or has_technical_punctuation
        ):
            terms.add(token.casefold())
    return terms


def _is_lexical_stem_variant(term1: str, term2: str) -> bool:
    """Return whether two general terms are close stem variants (e.g. rest/restful).

    Explicitly refuses known technology or scope terms to prevent false authorizations
    such as Java/JavaScript, SQL/MySQL/NoSQL, or pre-production/production.
    """
    strict_terms = _KNOWN_TECH_TERMS | _SCOPE_TERMS
    if term1 in strict_terms or term2 in strict_terms:
        return False
    shorter, longer = (term1, term2) if len(term1) <= len(term2) else (term2, term1)
    if len(shorter) < 3:
        return False
    if longer.startswith(shorter):
        suffix = longer[len(shorter) :]
        if len(suffix) <= 4 and suffix.isalpha():
            return True
    return False


def _required_ownership(text: str) -> tuple[int, str] | None:
    matches = [(rank, label) for pattern, rank, label in _OWNERSHIP_TERMS if pattern.search(text)]
    return max(matches) if matches else None


def _claim_index(
    ledger: dict[str, Any],
) -> tuple[dict[str, tuple[dict[str, Any], dict[str, Any]]], list[dict[str, str]]]:
    index: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    findings: list[dict[str, str]] = []
    for entity in ledger.get("entities", []):
        if not isinstance(entity, dict):
            findings.append(
                _finding("INVALID_LEDGER", "entities", "Ledger entity must be an object.")
            )
            continue
        for claim in entity.get("claims", []):
            if not isinstance(claim, dict) or not claim.get("claim_id"):
                findings.append(
                    _finding(
                        "INVALID_LEDGER",
                        str(entity.get("entity_id", "")),
                        "Claim must be an object with claim_id.",
                    )
                )
                continue
            claim_id = str(claim["claim_id"])
            if claim_id in index:
                findings.append(
                    _finding("DUPLICATE_CLAIM_ID", claim_id, "Claim ID must be unique.")
                )
            index[claim_id] = (entity, claim)
    return index, findings


def _declared_normalizations(entry: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    raw = entry.get("semantic_normalizations", [])
    if not isinstance(raw, list):
        return result
    for item in raw:
        if isinstance(item, dict):
            term = str(item.get("term", "")).casefold().strip()
            basis = str(item.get("basis", "")).strip()
            if term and basis:
                result[term] = basis
    return result


def audit_resume(
    resume: dict[str, Any],
    manifest: dict[str, Any],
    ledger: dict[str, Any],
    *,
    base_resume: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit manifest coverage, evidence state, metrics, tools, scope, and ownership."""
    validate_resume_content(resume, require_non_empty=True)
    findings: list[dict[str, str]] = []
    claim_index, ledger_findings = _claim_index(ledger)
    findings.extend(ledger_findings)

    expected_fingerprint = canonical_json_fingerprint(resume)
    if manifest.get("resume_fingerprint") != expected_fingerprint:
        findings.append(
            _finding(
                "STALE_MANIFEST",
                "resume_fingerprint",
                "Manifest fingerprint does not match the working resume.",
            )
        )

    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        entries = []
        findings.append(
            _finding("INVALID_MANIFEST", "entries", "Manifest entries must be an array.")
        )

    by_path: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            findings.append(
                _finding("INVALID_MANIFEST", "entries", "Each manifest entry must be an object.")
            )
            continue
        path = str(entry.get("projection_path", ""))
        if not path:
            findings.append(
                _finding(
                    "INVALID_MANIFEST", "entries", "Manifest entry is missing projection_path."
                )
            )
            continue
        if path in by_path:
            findings.append(
                _finding("DUPLICATE_MANIFEST_PATH", path, "Projection path must be unique.")
            )
        by_path[path] = entry

    fields = {
        path: (text, entity_type, entity_key)
        for path, text, entity_type, entity_key in iter_resume_text_fields(resume)
    }
    covered = 0
    for path, (text, entity_type, entity_key) in fields.items():
        entry = by_path.get(path)
        if entry is None:
            findings.append(
                _finding(
                    "MISSING_MANIFEST_ENTRY",
                    path,
                    "Substantive field has no Tailoring Manifest entry.",
                )
            )
            continue
        covered += 1
        if entry.get("rendered_text") != text:
            findings.append(
                _finding(
                    "MANIFEST_TEXT_MISMATCH",
                    path,
                    "Manifest rendered_text differs from the working resume.",
                )
            )
        if entry.get("operation") not in _ALLOWED_OPERATIONS:
            findings.append(
                _finding("INVALID_OPERATION", path, "Manifest operation is not recognized.")
            )

        expected_entity_id = stable_identifier(
            entity_type, entity_anchor(resume, entity_type, entity_key)[1]
        )
        if not entry.get("entity_id"):
            findings.append(
                _finding(
                    "MISSING_ENTITY_BINDING",
                    path,
                    "Substantive field must declare its Evidence Entity.",
                )
            )
        elif entry.get("entity_id") != expected_entity_id:
            findings.append(
                _finding(
                    "PATH_ENTITY_MISMATCH",
                    path,
                    f"Manifest entity `{entry.get('entity_id')}` does not match structural entity `{expected_entity_id}` for this path.",
                )
            )

        claim_ids = entry.get("source_claim_ids", [])
        if not isinstance(claim_ids, list) or not claim_ids:
            findings.append(
                _finding("UNSUPPORTED_FIELD", path, "Field has no supporting Atomic Claim IDs.")
            )
            continue
        supporting: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for claim_id in claim_ids:
            pair = claim_index.get(str(claim_id))
            if pair is None:
                findings.append(
                    _finding(
                        "UNKNOWN_CLAIM", path, f"Manifest references unknown claim {claim_id}."
                    )
                )
                continue
            entity, claim = pair
            if entity.get("state") != "active":
                findings.append(
                    _finding(
                        "INACTIVE_ENTITY", path, f"Claim {claim_id} belongs to an inactive entity."
                    )
                )
            if claim.get("status") != "active":
                findings.append(
                    _finding("INACTIVE_CLAIM", path, f"Claim {claim_id} is not active.")
                )
            if claim.get("evidence_state") not in _ALLOWED_EVIDENCE_STATES:
                findings.append(
                    _finding(
                        "UNRESOLVED_EVIDENCE",
                        path,
                        f"Claim {claim_id} is {claim.get('evidence_state')}.",
                    )
                )
            declared_entity = entry.get("entity_id")
            if declared_entity and declared_entity != entity.get("entity_id"):
                findings.append(
                    _finding(
                        "ENTITY_MISMATCH",
                        path,
                        f"Claim {claim_id} belongs to another Evidence Entity.",
                    )
                )
            supporting.append(pair)
        if not supporting:
            continue

        claim_text = "\n".join(str(claim.get("claim_text", "")) for _, claim in supporting)
        claim_metric_values = _metrics(claim_text)
        for _, claim in supporting:
            for metric in claim.get("metrics", []):
                if isinstance(metric, dict) and metric.get("value"):
                    claim_metric_values.add(_normalize_metric(str(metric["value"])))
        for metric in _metrics(text) - claim_metric_values:
            findings.append(
                _finding(
                    "UNSUPPORTED_METRIC",
                    path,
                    f"Metric `{metric}` is not present in supporting claims for this entity.",
                )
            )

        supported_terms = _mentioned_terms(claim_text)
        for _, claim in supporting:
            supported_terms.update(str(tool).casefold() for tool in claim.get("tools", []))
        normalizations = _declared_normalizations(entry)
        for term in _mentioned_terms(text) - supported_terms:
            if term in normalizations and term in _NORMALIZABLE_CONCEPTS:
                continue
            # Tolerate close morphological stem variants for general terms (e.g. REST vs RESTful).
            if any(_is_lexical_stem_variant(term, supported) for supported in supported_terms):
                continue
            code = "UNSUPPORTED_SCOPE" if term in _SCOPE_TERMS else "TOOL_DRIFT"
            findings.append(
                _finding(
                    code,
                    path,
                    f"Term `{term}` is absent from supporting claims and semantic normalizations.",
                )
            )

        required = _required_ownership(text)
        if required is not None:
            required_rank, required_label = required
            available_rank = max(
                _OWNERSHIP_RANK.get(str(claim.get("ownership_level", "contributed")), 0)
                for _, claim in supporting
            )
            if required_rank > available_rank:
                findings.append(
                    _finding(
                        "ROLE_INFLATION",
                        path,
                        f"Rendered ownership `{required_label}` exceeds supporting claim ownership.",
                    )
                )

    for path in sorted(set(by_path) - set(fields)):
        findings.append(
            _finding(
                "EXTRA_MANIFEST_ENTRY",
                path,
                "Manifest path is not a non-empty field in the working resume.",
            )
        )

    if base_resume is not None:
        clean_base = dict(base_resume)
        clean_base.pop("source_fingerprint", None)
        clean_base.pop("captured_at", None)
        base_pairs = {(path, text) for path, text, _, _ in iter_resume_text_fields(clean_base)}
        current_pairs = {(path, text) for path, (text, _, _) in fields.items()}
        required_removals = base_pairs - current_pairs
        removed = manifest.get("removed_entries", [])
        removed_pairs = (
            {
                (str(item.get("source_path", "")), str(item.get("source_text", "")))
                for item in removed
                if isinstance(item, dict)
            }
            if isinstance(removed, list)
            else set()
        )
        for path, _ in sorted(required_removals - removed_pairs):
            findings.append(
                _finding(
                    "UNRECORDED_REMOVAL",
                    path,
                    "Source field removal or replacement is absent from the manifest.",
                )
            )

    verdict = "PASS" if not findings else "FAIL"
    return {
        "verdict": verdict,
        "findings": findings,
        "coverage": {
            "covered_fields": covered,
            "total_fields": len(fields),
            "coverage_percent": round(100 * covered / len(fields), 1) if fields else 100.0,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a tailored resume against candidate evidence."
    )
    parser.add_argument("--resume", required=True, help="Path to resume-working.json")
    parser.add_argument("--manifest", required=True, help="Path to resume-changes.json")
    parser.add_argument("--evidence", required=True, help="Path to candidate-evidence.json")
    parser.add_argument("--base", help="Optional path to base-resume.json")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = audit_resume(
            load_json_file(Path(args.resume).expanduser().resolve()),
            load_json_file(Path(args.manifest).expanduser().resolve()),
            load_json_file(Path(args.evidence).expanduser().resolve()),
            base_resume=(
                load_json_file(Path(args.base).expanduser().resolve()) if args.base else None
            ),
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: factual audit failed: {exc}", file=sys.stderr)
        return 1
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Factual audit: {report['verdict']}")
        for finding in report["findings"]:
            print(f"  ✗ [{finding['code']}] {finding['path']}: {finding['message']}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
