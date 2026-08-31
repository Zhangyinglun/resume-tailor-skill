# Resume Tailoring Data Contracts

All personalized files live under `USER_WORKSPACE/cache/`. One workspace represents one candidate. The Skill package never stores candidate data.

## Source Snapshot: `base-resume.json`

The immutable structured parse of the latest source resume. It uses the Tailored Resume display structure below and adds:

```json
{
  "source_fingerprint": "sha256:...",
  "captured_at": "2026-01-01T00:00:00Z"
}
```

A new source resume creates a new snapshot through ledger synchronization. It never discards candidate-confirmed claims.

## Candidate Evidence Ledger: `candidate-evidence.json`

```json
{
  "schema_version": 1,
  "candidate_id": "candidate-...",
  "base_source_fingerprint": "sha256:...",
  "entities": [
    {
      "entity_id": "experience-...",
      "entity_type": "experience",
      "label": "Company — Role",
      "state": "active",
      "claims": [
        {
          "claim_id": "claim-...",
          "claim_type": "responsibility",
          "claim_text": "Implemented a Redis-backed cache.",
          "evidence_state": "sourced",
          "provenance": {
            "source_type": "source_snapshot",
            "source_fingerprint": "sha256:...",
            "source_path": "experience[0].bullets[0]",
            "original_excerpt": "Implemented a Redis-backed cache."
          },
          "tools": ["Redis"],
          "metrics": [],
          "ownership_level": "implemented",
          "confirmed_at": null,
          "revoked_at": null,
          "supersedes": []
        }
      ]
    }
  ]
}
```

Allowed evidence states are `sourced`, `candidate_confirmed`, `needs_confirmation`, and `unsupported`. Only active `sourced` and `candidate_confirmed` claims may support published text. Claims are never physically overwritten: corrections revoke or supersede earlier claims.

Every metric is stored on a claim inside its Evidence Entity. Metrics cannot be transferred between entities.

## Candidate Profile: `candidate-profile.json`

Stores cross-JD presentation preferences, target direction, preferred project aliases, emphasis/de-emphasis choices, and excluded optional profile fields. It is not a factual evidence source and cannot authorize a resume claim.

## JD Analysis: `jd-analysis.json`

```json
{
  "position": "Target Role",
  "keywords": {"P1": [], "P2": [], "P3": []},
  "capabilities": [
    {
      "capability_id": "cap-...",
      "priority": "P1",
      "name": "Distributed systems design",
      "match_type": "direct",
      "evidence_state": "candidate_confirmed",
      "claim_ids": ["claim-..."],
      "clarification": null
    }
  ],
  "alignment": {"matched": [], "transferable": [], "gaps": []}
}
```

`match_type` is one of `direct`, `semantic_equivalent`, `transferable`, or `gap`. Capability `evidence_state` follows the Ledger vocabulary. A P1/P2 capability in `needs_confirmation` may trigger a clarification; `unsupported` remains a Gap.

## Tailored Resume: `resume-working.json`

This is a pure display projection with no internal IDs:

```json
{
  "name": "FULL NAME",
  "contact": "City | Phone | Email | LinkedIn",
  "summary": "Evidence-grounded summary.",
  "skills": [{"category": "Languages", "items": "Python, Go"}],
  "experience": [{
    "company": "Company",
    "title": "Title",
    "location": "Location",
    "dates": "Dates",
    "bullets": ["Evidence-grounded bullet"]
  }],
  "projects": [{
    "name": "Project",
    "tech": "Python",
    "dates": "2024",
    "bullets": ["Evidence-grounded bullet"]
  }],
  "education": [{"school": "School", "degree": "Degree", "dates": "Dates"}],
  "certifications": [{"name": "Certification", "issuer": "Issuer", "dates": "Dates"}],
  "awards": [{"name": "Award", "organization": "Organization", "dates": "Dates"}]
}
```

Required keys are `name`, `contact`, `summary`, `skills`, `experience`, and `education`. Optional sections are arrays when present. Every nested display value is a string except arrays and objects.

## Tailoring Manifest: `resume-changes.json`

The manifest covers every non-empty substantive leaf in the Tailored Resume, including unchanged, added, rewritten, merged, deleted, and reordered content.

```json
{
  "schema_version": 1,
  "target_jd_fingerprint": "sha256:...",
  "resume_fingerprint": "sha256:...",
  "entries": [
    {
      "projection_path": "experience[0].bullets[0]",
      "operation": "REWORD",
      "rendered_text": "Implemented a Redis-backed cache for document retrieval.",
      "entity_id": "experience-...",
      "source_claim_ids": ["claim-..."],
      "match_type": "semantic_equivalent",
      "semantic_normalizations": [
        {
          "term": "RAG",
          "basis": "The active claims explicitly describe document retrieval before generation."
        }
      ],
      "reason": "Aligns an evidenced capability to the target terminology."
    }
  ],
"removed_entries": [],
"warning_dispositions": [
{
"finding": "bullet_density",
"status": "accepted",
"reason": "Two-entry resume; density target not applicable."
}
]
}
```

`warning_dispositions` resolves advisory content-QA findings (for example `bullet_density`). Each entry records the check `name` in `finding`, sets `status` to `accepted`, and supplies a non-empty `reason`. A disposition applies only to advisory content warnings; it can never suppress a factual-audit finding.

Each `projection_path` must be unique. The `rendered_text` must equal the value at that path. Contact/profile preferences may use a dedicated sourced profile claim; preferences alone never authorize tools, ownership, completion status, or metrics.

Manual edits require manifest regeneration. Automatic rebuilding may link only exact existing claim text; unresolved fields become blocking audit findings and require correction or candidate evidence.
