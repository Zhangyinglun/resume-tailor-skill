# Model-Driven Projection Planning & Language Optimization Protocol

This protocol defines the host-model contracts, structured artifacts, and validation rules for evidence-bound resume tailoring. Host models perform capability reasoning, space budgeting, and technical resume language optimization. Deterministic Python scripts validate schemas, verify evidence links, calculate fingerprints, and enforce factual integrity without making network calls or embedding model SDKs.

---

## 1. Pipeline Inputs

The host model consumes the following artifacts from `USER_WORKSPACE/cache/`:

1. **JD Analysis** (`jd-analysis.json`): Target role title, P1/P2/P3 keywords, capabilities, match types (`direct`, `semantic_equivalent`, `transferable`, `gap`), and evidence states (`sourced`, `candidate_confirmed`, `needs_confirmation`, `unsupported`).
2. **Candidate Evidence Ledger** (`candidate-evidence.json`): Durable single source of truth containing active entities and atomic claims. Only active claims with state `sourced` or `candidate_confirmed` (and `revoked_at: null`) can authorize resume content.
3. **Candidate Profile** (`candidate-profile.json`): Career positioning preferences, project display aliases, and styling preferences (presentation guidance only; cannot authorize factual claims).
4. **Source Snapshot** (`base-resume.json`): Immutable parse of the original resume establishing baseline formal employment entities, education, and structure.
5. **Page Constraints**: Target page size `A4`, target page count `1`, formal employment bullet range `1–5` per entry, skills groups `2–4` (rendering to `2–4` body lines), max `5` clarification questions, max `3` Content Fit revisions.

---

## 2. Model Execution Stages

The model-driven tailoring process executes in three distinct stages:

```text
[JD Analysis + Active Ledger + Profile + Snapshot]
                      │
                      ▼
        Stage 1: Clarification Inquiry (optional)
        - Evaluate missing/unconfirmed P1/P2 capabilities
        - If high-leverage gaps exist: produce status "needs_clarification" (1-5 questions)
        - Ingest candidate answers into Candidate Evidence Ledger
                      │
                      ▼
        Stage 2: Projection Planning (Planner)
        - Allocate presentation importance (critical / important / supporting)
        - Formulate Content Intents bound to active claim IDs and JD capability IDs
        - Plan 2-4 dynamic Skill Presentation Groups with item-level claim links
        - Decide optional section inclusions/removals
        - Output: cache/projection-plan.json (status "ready" or "revision_required")
                      │
                      ▼
        Stage 3: Resume Language Optimization (Optimizer)
        - Transform each Content Intent into concise, recruiter-facing resume text
        - Apply technical resume register and adopted plain-language patterns
        - Run meaning-preservation self-check (facts_added=[], metrics_changed=[], etc.)
        - Output: cache/projection-language.json
                      │
                      ▼
        Deterministic Materialization & Factual Audit
        - python3 scripts/projection_plan_manager.py build ...
```

---

## 3. Projection Plan Schema (`projection-plan.json`)

The Projection Plan records target-specific content budget decisions before final prose generation.

### Plan Statuses

- `needs_clarification`: Contains 1–5 high-leverage questions targeting missing P1/P2 capabilities. Final projection cannot build until answers are ingested or gaps confirmed.
- `ready`: All intents are bound to active claims; ready for Language Optimization and materialization.
- `revision_required`: Geometry feedback from a temporary render requires content revision (Revision 2 or 3).

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ProjectionPlan",
  "type": "object",
  "required": [
    "schema_version",
    "revision",
    "status",
    "target_jd_fingerprint",
    "source_snapshot_fingerprint",
    "constraints",
    "clarifications",
    "summary_intent",
    "experience_plans",
    "skills_plan",
    "optional_sections",
    "next_cuts"
  ],
  "properties": {
    "schema_version": { "type": "integer", "enum": [1] },
    "revision": { "type": "integer", "minimum": 1, "maximum": 3 },
    "status": {
      "type": "string",
      "enum": ["needs_clarification", "ready", "revision_required"]
    },
    "target_jd_fingerprint": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
    "source_snapshot_fingerprint": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
    "constraints": {
      "type": "object",
      "properties": {
        "page_size": { "type": "string", "enum": ["A4"] },
        "page_count": { "type": "integer", "enum": [1] },
        "experience_bullet_min": { "type": "integer", "enum": [1] },
        "experience_bullet_max": { "type": "integer", "enum": [5] },
        "skills_group_min": { "type": "integer", "enum": [2] },
        "skills_group_max": { "type": "integer", "enum": [4] },
        "skills_rendered_line_min": { "type": "integer", "enum": [2] },
        "skills_rendered_line_max": { "type": "integer", "enum": [4] },
        "clarification_question_max": { "type": "integer", "enum": [5] },
        "content_fit_revision_max": { "type": "integer", "enum": [3] }
      }
    },
    "clarifications": {
      "type": "array",
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["question_id", "question", "capability_ids"],
        "properties": {
          "question_id": { "type": "string" },
          "question": { "type": "string" },
          "capability_ids": { "type": "array", "items": { "type": "string" } },
          "entity_id": { "type": "string" },
          "context": { "type": "string" }
        }
      }
    },
    "summary_intent": {
      "type": "object",
      "required": ["intent_id", "claim_ids", "capability_ids", "operation", "content_intent"],
      "properties": {
        "intent_id": { "type": "string" },
        "claim_ids": { "type": "array", "items": { "type": "string" } },
        "capability_ids": { "type": "array", "items": { "type": "string" } },
        "operation": { "type": "string" },
        "content_intent": { "type": "string" },
        "target_lines": { "type": "integer", "minimum": 1 }
      }
    },
    "experience_plans": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["entity_id", "importance", "target_bullet_count", "reason", "content_intents"],
        "properties": {
          "entity_id": { "type": "string" },
          "importance": { "type": "string", "enum": ["critical", "important", "supporting"] },
          "target_bullet_count": { "type": "integer", "minimum": 1, "maximum": 5 },
          "reason": { "type": "string" },
          "content_intents": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["intent_id", "claim_ids", "capability_ids", "operation", "content_intent"],
              "properties": {
                "intent_id": { "type": "string" },
                "claim_ids": { "type": "array", "items": { "type": "string" } },
                "capability_ids": { "type": "array", "items": { "type": "string" } },
                "operation": { "type": "string" },
                "content_intent": { "type": "string" },
                "target_lines": { "type": "integer", "minimum": 1 }
              }
            }
          }
        }
      }
    },
    "skills_plan": {
      "type": "object",
      "required": ["groups"],
      "properties": {
        "groups": {
          "type": "array",
          "minItems": 2,
          "maxItems": 4,
          "items": {
            "type": "object",
            "required": ["category", "items"],
            "properties": {
              "category": { "type": "string" },
              "items": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["display_term", "claim_ids"],
                  "properties": {
                    "display_term": { "type": "string" },
                    "claim_ids": { "type": "array", "items": { "type": "string" } },
                    "capability_ids": { "type": "array", "items": { "type": "string" } },
                    "basis": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    },
    "optional_sections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["section", "decision", "reason"],
        "properties": {
          "section": { "type": "string" },
          "decision": { "type": "string", "enum": ["keep", "remove", "compress"] },
          "reason": { "type": "string" },
          "entity_ids": { "type": "array", "items": { "type": "string" } },
          "content_intents": { "type": "array" }
        }
      }
    },
    "next_cuts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["target", "estimated_line_savings", "reason"],
        "properties": {
          "target": { "type": "string" },
          "estimated_line_savings": { "type": "integer" },
          "reason": { "type": "string" }
        }
      }
    }
  }
}
```

---

## 4. Language Output Schema (`projection-language.json`)

The Resume Language Optimizer converts Content Intents into recruiter-facing text without altering factual claims, tools, metrics, scope, environment, or ownership.

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ProjectionLanguageOutput",
  "type": "object",
  "required": [
    "schema_version",
    "plan_revision",
    "target_jd_fingerprint",
    "items"
  ],
  "properties": {
    "schema_version": { "type": "integer", "enum": [1] },
    "plan_revision": { "type": "integer", "minimum": 1, "maximum": 3 },
    "target_jd_fingerprint": { "type": "string", "pattern": "^sha256:[a-f0-9]{64}$" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "intent_id",
          "rendered_text",
          "source_claim_ids",
          "style_actions",
          "meaning_check"
        ],
        "properties": {
          "intent_id": { "type": "string" },
          "rendered_text": { "type": "string" },
          "source_claim_ids": { "type": "array", "items": { "type": "string" } },
          "style_actions": { "type": "array", "items": { "type": "string" } },
          "meaning_check": {
            "type": "object",
            "required": [
              "facts_added",
              "facts_removed",
              "metrics_changed",
              "ownership_changed"
            ],
            "properties": {
              "facts_added": { "type": "array", "maxItems": 0 },
              "facts_removed": { "type": "array", "maxItems": 0 },
              "metrics_changed": { "type": "array", "maxItems": 0 },
              "ownership_changed": { "type": "boolean", "enum": [false] }
            }
          }
        }
      }
    }
  }
}
```

---

## 5. Skills Item Array & Presentation Group Binding

Skills in the tailored resume are structured as an array of items rather than unparsed comma-separated strings:

```json
{
  "skills": [
    {
      "category": "AI Platforms & Tooling",
      "items": ["Azure OpenAI", "MCP", "RAG", "Evals"]
    },
    {
      "category": "Backend & Distributed Systems",
      "items": ["Python", "Go", "Redis", "Kafka"]
    }
  ]
}
```

### Presentation vs. Entity Binding

1. **Item-Level Manifest Binding (`skills[i].items[j]`)**:
   - Uses `binding_mode: "single_entity"`.
   - Binds directly to the Evidence Entity and active Atomic Claim IDs backing that specific skill (e.g. `claim-azure-openai` on `experience-example-corp`).
   - Enables fine-grained audit: every displayed skill must be verified by a distinct claim.
2. **Category-Level Manifest Binding (`skills[i].category`)**:
   - Uses `binding_mode: "presentation"`.
   - The category label (e.g., `"AI Platforms & Tooling"`) is target-specific presentation metadata, NOT a candidate fact or Evidence Entity.
   - The manifest entry references the constituent item paths (e.g., `["skills[0].items[0]", "skills[0].items[1]"]`) and a justification.
   - Factual auditing verifies that any technical term in the category label is supported by at least one bound item in the group.

Legacy string format (`"items": "Azure OpenAI, MCP, RAG"`) is automatically normalized into an item array during ingestion and planning while preserving full backward compatibility.

---

## 6. Budgeting Rules & Model Decision Heuristics

### Deterministic Hard Constraints

- **Formal Experience Coverage**: Every formal employment entity present in the Source Snapshot MUST be represented in the Projection Plan with 1–5 bullets. No formal employer may be deleted.
- **Experience Bullets**: 1 to 5 bullets per formal employment entry.
- **Skill Groups**: 2 to 4 Skill Presentation Groups.
- **Rendered Skills Lines**: Under the preferred readable layout, Skills body text must render to 2–4 physical lines (excluding section header).
- **Single-Entity Claims**: A single Content Intent cannot combine claims from multiple different Evidence Entities.
- **Clarification Limit**: At most 5 clarification questions in a `needs_clarification` plan.
- **Revision Limit**: At most 3 Content Fit revisions before publication.

### Importance Allocation Heuristics

- `critical` experience: 3–5 bullets (carries primary P1/P2 evidence).
- `important` experience: 2–3 bullets (carries secondary or supporting P2 capabilities).
- `supporting` experience: 1 bullet (older or less directly relevant formal employment retained to maintain chronological integrity).

### Optional Sections

Sections such as `projects`, `awards`, `certifications`, or `patents` may be retained, compressed, or completely removed (`decision: "remove"`) if their marginal value to the target JD is low.

---

## 7. Content Fit & Revision Protocol

When the temporary readable render produces geometry feedback, the model revises the plan based on measured geometry rather than character-count heuristics.

### Overflow Revision Order (Content Reduction)

When verdict is `overflow` (page_count > 1 or bottom margin exceeded):

1. **Remove low-value optional sections**: Drop standalone `awards`, `patents`, or `projects` that do not cover critical P1/P2 capabilities.
2. **Prune low-value skills**: Remove P3 tools or items already demonstrated in experience bullets.
3. **Merge overlapping intents**: Combine related claims within the same Evidence Entity into tighter compound statements.
4. **Shorten supporting bullets**: Reduce target line counts on supporting experience bullets.
5. **Compress supporting experience**: Reduce supporting employment entities to exactly 1 high-impact bullet.
6. **Compress important experience**: Trim secondary bullets only after low-value options are exhausted.

### Underfill Revision Order (Content Expansion)

When verdict is `underfill` (sparse layout or excessive bottom whitespace):

1. **Add unused high-value claims**: Check the ledger for unused active claims in critical experience entities.
2. **Restore compressed P1/P2 contributions**: Expand 1-bullet entries to 2 bullets where strong evidence exists.
3. **Add verified relevant skills**: Include evidenced foundational or secondary technical skills.
4. **Stop when high-value evidence is exhausted**: If no further strong evidence exists, accept the content and permit layout auto-fit to adjust spacing cleanly.

---

## 8. Selective Rewrite Stability Rules

Content Fit revisions (Revision 2 and 3) must NOT cause wholesale text rewrites:

1. **Wording Stability**: Any `intent_id` whose `claim_ids`, `capability_ids`, `content_intent`, and `target_lines` are unchanged between revisions MUST retain identical `rendered_text`.
2. **Diff Isolation**: Modifications must be strictly confined to new, pruned, or intentionally resized intents.
3. **Deterministic Enforcement**: `projection_plan_manager.py` verifies stability across revisions and rejects unrelated wording drift.

---

## 9. Failure Branches & Error Handling

| Phase | Failure Condition | Action / Result |
| --- | --- | --- |
| **Planning** | Stale JD/Snapshot fingerprint, missing formal experience entity, invalid claim IDs, >5 questions | Script exits with error; working projection and manifest remain untouched. |
| **Clarification** | Plan status is `needs_clarification` | Script exits with status 2; outputs questions; halts build until answers ingested. |
| **Language** | Missing/extra intent, claim mismatch, chatbot/first-person phrasing, placeholder text, drift on unchanged intent | Build fails with error; working cache is preserved intact. |
| **Language Self-Check** | `facts_added`, `facts_removed`, `metrics_changed` non-empty, or `ownership_changed: true` | Build fails immediately prior to projection write. |
| **Audit** | Unlinked field, metric drift, cross-entity metric reuse, tool inflation | `audit_factual_integrity.py` blocks compilation (exit 1). |
| **Content Fit** | 3 revisions exhausted with unacceptable geometry | Last candidate PDF retained in `rejected/`; previous Accepted Resume preserved. |
| **Publication** | Programmatic or visual QA failure | Compilation aborted; prior Accepted Resume untouched. |

---

## 10. Synthetic Plan & Language Examples

> Note: Synthetic candidate data only. No personal or real candidate information.

### Scenario A: Target Role — OpenAI Applied AI Engineer (Tool Calling & Plugins)

**Candidate Background**: Synthetic candidate with experience in distributed backend engineering, MCP tooling, Azure OpenAI integrations, and caching.

#### Projection Plan Excerpt (`cache/projection-plan.json`)

```json
{
  "schema_version": 1,
  "revision": 1,
  "status": "ready",
  "target_jd_fingerprint": "sha256:4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a",
  "source_snapshot_fingerprint": "sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
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
    "content_fit_revision_max": 3
  },
  "clarifications": [],
  "summary_intent": {
    "intent_id": "intent-summary-ai-applied",
    "claim_ids": ["claim-profile-engineer-role", "claim-mcp-summary"],
    "capability_ids": ["cap-p1-tool-calling", "cap-p2-agentic-workflow"],
    "operation": "EMPHASIZE",
    "content_intent": "Applied AI engineer with expertise in tool calling, MCP servers, and LLM diagnostic workflows.",
    "target_lines": 2
  },
  "experience_plans": [
    {
      "entity_id": "experience-apex-systems",
      "importance": "critical",
      "target_bullet_count": 3,
      "reason": "Contains strongest P1 evidence for tool calling, MCP integration, and Azure OpenAI telemetry.",
      "content_intents": [
        {
          "intent_id": "intent-apex-mcp-tools",
          "claim_ids": ["claim-apex-mcp-1", "claim-apex-azure-openai"],
          "capability_ids": ["cap-p1-tool-calling"],
          "operation": "EMPHASIZE",
          "content_intent": "Developed an MCP diagnostic server with Azure OpenAI tool calling for automated incident analysis.",
          "target_lines": 2
        },
        {
          "intent_id": "intent-apex-evals",
          "claim_ids": ["claim-apex-eval-benchmarks"],
          "capability_ids": ["cap-p2-evaluation-benchmarks"],
          "operation": "LEAD_WITH",
          "content_intent": "Built automated evaluation pipelines for prompt and tool invocation reliability.",
          "target_lines": 1
        },
        {
          "intent_id": "intent-apex-latency",
          "claim_ids": ["claim-apex-redis-latency"],
          "capability_ids": ["cap-p2-latency-optimization"],
          "operation": "QUANTIFY",
          "content_intent": "Reduced tool invocation retrieval latency by 35% using distributed Redis caching.",
          "target_lines": 1
        }
      ]
    },
    {
      "entity_id": "experience-beacon-labs",
      "importance": "supporting",
      "target_bullet_count": 1,
      "reason": "Earlier backend role; compressed to 1 bullet to maintain chronological continuity.",
      "content_intents": [
        {
          "intent_id": "intent-beacon-backend",
          "claim_ids": ["claim-beacon-api-gateway"],
          "capability_ids": ["cap-p3-rest-api"],
          "operation": "DOWNPLAY",
          "content_intent": "Maintained high-throughput REST APIs and microservice routing infrastructure.",
          "target_lines": 1
        }
      ]
    }
  ],
  "skills_plan": {
    "groups": [
      {
        "category": "AI Platforms & Tooling",
        "items": [
          {
            "display_term": "Azure OpenAI",
            "claim_ids": ["claim-apex-azure-openai"],
            "capability_ids": ["cap-p1-tool-calling"],
            "basis": "P1 direct requirement"
          },
          {
            "display_term": "Model Context Protocol (MCP)",
            "claim_ids": ["claim-apex-mcp-1"],
            "capability_ids": ["cap-p1-tool-calling"],
            "basis": "P1 core capability"
          },
          {
            "display_term": "Evaluation Pipelines",
            "claim_ids": ["claim-apex-eval-benchmarks"],
            "capability_ids": ["cap-p2-evaluation-benchmarks"],
            "basis": "P2 evals requirement"
          }
        ]
      },
      {
        "category": "Backend & Infrastructure",
        "items": [
          {
            "display_term": "Python",
            "claim_ids": ["claim-skills-python"],
            "capability_ids": ["cap-p1-tool-calling"],
            "basis": "Primary development language"
          },
          {
            "display_term": "Redis",
            "claim_ids": ["claim-apex-redis-latency"],
            "capability_ids": ["cap-p2-latency-optimization"],
            "basis": "Used in tool caching"
          },
          {
            "display_term": "Docker",
            "claim_ids": ["claim-skills-docker"],
            "capability_ids": ["cap-p3-containerization"],
            "basis": "Supporting infrastructure"
          }
        ]
      }
    ]
  },
  "optional_sections": [
    {
      "section": "awards",
      "decision": "remove",
      "reason": "Standalone academic award omitted to allocate space for critical MCP and eval capabilities."
    }
  ],
  "next_cuts": [
    {
      "target": "experience-beacon-labs.bullets[0]",
      "estimated_line_savings": 1,
      "reason": "Compress supporting experience if layout overflows."
    }
  ]
}
```

#### Language Output Excerpt (`cache/projection-language.json`)

```json
{
  "schema_version": 1,
  "plan_revision": 1,
  "target_jd_fingerprint": "sha256:4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a",
  "items": [
    {
      "intent_id": "intent-summary-ai-applied",
      "rendered_text": "Applied AI Engineer with extensive experience developing Model Context Protocol (MCP) servers, tool calling workflows, and automated LLM evaluation pipelines on Azure OpenAI.",
      "source_claim_ids": ["claim-profile-engineer-role", "claim-mcp-summary"],
      "style_actions": ["lead_with_evidence", "remove_fluff"],
      "meaning_check": {
        "facts_added": [],
        "facts_removed": [],
        "metrics_changed": [],
        "ownership_changed": false
      }
    },
    {
      "intent_id": "intent-apex-mcp-tools",
      "rendered_text": "Architected an MCP diagnostic server on Azure OpenAI, implementing structured tool calling to automate telemetry inspection and root-cause analysis across production services.",
      "source_claim_ids": ["claim-apex-mcp-1", "claim-apex-azure-openai"],
      "style_actions": ["specific_verb", "clear_system_context"],
      "meaning_check": {
        "facts_added": [],
        "facts_removed": [],
        "metrics_changed": [],
        "ownership_changed": false
      }
    },
    {
      "intent_id": "intent-apex-evals",
      "rendered_text": "Built automated evaluation pipelines to benchmark tool invocation accuracy, schema conformance, and prompt regression rates.",
      "source_claim_ids": ["claim-apex-eval-benchmarks"],
      "style_actions": ["direct_action", "evidence_first"],
      "meaning_check": {
        "facts_added": [],
        "facts_removed": [],
        "metrics_changed": [],
        "ownership_changed": false
      }
    },
    {
      "intent_id": "intent-apex-latency",
      "rendered_text": "Reduced tool invocation retrieval latency by 35% by implementing a distributed Redis caching layer for contextual embeddings.",
      "source_claim_ids": ["claim-apex-redis-latency"],
      "style_actions": ["quantified_impact", "preserved_metric"],
      "meaning_check": {
        "facts_added": [],
        "facts_removed": [],
        "metrics_changed": [],
        "ownership_changed": false
      }
    },
    {
      "intent_id": "intent-beacon-backend",
      "rendered_text": "Maintained high-throughput REST APIs and microservice routing infrastructure handling 10k+ daily transactions.",
      "source_claim_ids": ["claim-beacon-api-gateway"],
      "style_actions": ["concise_supporting"],
      "meaning_check": {
        "facts_added": [],
        "facts_removed": [],
        "metrics_changed": [],
        "ownership_changed": false
      }
    }
  ]
}
```

---

### Scenario B: Target Role — Principal Distributed Systems Engineer (High-Throughput Infrastructure)

Same synthetic candidate ledger projected against a Distributed Systems JD. Note the dynamic shift in importance, Skills groupings, and bullet emphasis.

#### Projection Plan Highlights

- **Skills Groups**: Shifted to `"Distributed Systems & Storage"` (Redis, Kafka, PostgreSQL) and `"Cloud & Reliability"` (Go, Kubernetes, Prometheus). MCP and LLM items are deprioritized.
- **Experience Allocation**: `experience-apex-systems` emphasizes the distributed caching layer and concurrency throughput; `experience-beacon-labs` API gateway role is upgraded to `important` with 2 bullets emphasizing fault tolerance and scale.
- **Optional Sections**: Retained patent on distributed lock management; dropped unrelated side projects.
