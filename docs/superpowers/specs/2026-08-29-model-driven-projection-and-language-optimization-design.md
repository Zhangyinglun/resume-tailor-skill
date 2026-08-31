# Model-driven projection and resume language optimization

- Status: Approved design, pending implementation plan
- Date: 2026-08-29
- Scope: `monkey-resume` Skill package
- Acceptance fixture: Yinglun Zhang targeting OpenAI Applied AI Engineer, Plugins

## 1. Context

The current Skill decomposes Job Descriptions into P1/P2/P3 capabilities, preserves candidate evidence in the Candidate Evidence Ledger, records tailoring operations in the Tailoring Manifest, audits factual integrity, and renders a verified single-page A4 PDF.

It does not yet have a deterministic workflow seam for model-driven content budgeting. Agents can manually lead with relevant experience, remove low-value content, and rewrite Skills, but the scripts do not automatically turn JD Capability links into a target-specific Projection Plan. The existing `score_all_bullets()` helper assigns lexical P1/P2/P3 scores, but it is not connected to projection generation and misses semantically matched evidence when JD phrases differ from resume wording.

The project also needs a resume-specific natural-language layer. Generic LLM output can read as templated or promotional even when it is factual. General-purpose Humanizer Skills contain useful editing patterns, but many of their voice-injection and detector-evasion techniques are unsuitable for resumes.

## 2. Goals

1. Use the host model to decide which evidence matters for a target JD, without a fixed keyword-weight formula.
2. Allocate more content to high-value Evidence Entities and less content to low-value entities while preserving complete employment chronology.
3. Generate dynamic Skills containing only target-relevant, evidence-supported, or role-foundational capabilities.
4. Produce concise, natural, recruiter-facing English without changing candidate facts.
5. Fit the strongest evidence into one A4 page by revising content before layout compression.
6. Preserve complete Tailoring Manifest coverage and the mandatory factual audit.
7. Keep model-provider integration outside the Python package: the host Agent supplies structured planning and language artifacts.
8. Preserve the previous Accepted Resume whenever planning, auditing, content fit, rendering, or QA fails.

## 3. Non-goals

- Predicting or gaming a third-party ATS ranking algorithm.
- Optimizing against GPTZero, Turnitin, ZeroGPT, or another AI detector.
- Making prose look human through typos, slang, uncommon synonyms, artificial sentence-length variance, or grammatical errors.
- Allowing the model to infer tools, metrics, scope, ownership, environment, production state, or completion state from the JD.
- Removing a formal employment entry and creating an unexplained chronology gap.
- Letting `--auto-fit` change resume content.
- Adding a model SDK, API key, provider adapter, or network call to the bundled Python scripts.

## 4. Approved product decisions

1. Use capability-linked, model-driven planning rather than fixed lexical relevance scores.
2. Keep every formal employment entry with company, title, dates, and at least one bullet.
3. Allow Projects, Awards, Patents, and other optional sections to be removed when they have low marginal value.
4. Allow at most three to five high-leverage clarification questions before final planning.
5. Always target one A4 page.
6. Apply content decisions automatically. Explain every material addition, merge, reorder, downplay, and removal in the Tailoring Manifest and final report.
7. Generate two to four dynamic Skills groups using the evidence-chain policy.
8. Preserve canonical tool and language names in Skills.
9. Use a dedicated Resume Language Optimizer after evidence selection and before the factual audit.
10. Treat AI-writing pattern checks as explainable editing signals, not authorship classifiers.
11. Evolve Skills from one comma-delimited string to individually auditable display items while accepting the legacy string form on input.

## 5. Domain model

### Projection Plan

A target-specific, evidence-bound decision record that selects Content Intents, assigns presentation importance, budgets resume space, and decides which optional content to retain, merge, or remove.

### Content Intent

An instruction describing what one Tailored Resume element must communicate, which Atomic Claims and JD Capabilities support it, and how much space it should receive. It does not contain final prose.

### Resume Language Optimization

A meaning-preserving transformation from Content Intents to concise, natural, recruiter-facing display text. It must preserve evidence scope, canonical technical terms, metrics, and ownership.

### Skill Presentation Group

A target-specific display grouping whose category label organizes individually evidence-bound Skill items. The category is presentation metadata, not an Evidence Entity or a factual claim about the candidate.

### Content Fit Feedback

Measured Candidate PDF geometry indicating overflow, underfill, or fit. It informs a revised Projection Plan; it is not a character-count estimate or an auto-fit score.

## 6. Architecture

```text
Source Snapshot + Candidate Evidence Ledger + Candidate Profile
                              +
                        JD Analysis
                              |
                              v
                  Host-model Projection Planner
                  - select evidence
                  - assign module importance
                  - allocate content budget
                  - decide Skills and optional sections
                              |
                              v
                   cache/projection-plan.json
                              |
                              v
                Host-model Resume Language Optimizer
                - technical resume register
                - concise natural wording
                - meaning-preservation self-check
                              |
                              v
                 cache/projection-language.json
                              |
                              v
                  Projection Plan Manager
                  - deterministic validation
                  - materialize Tailored Resume
                  - materialize Tailoring Manifest
                              |
                 +------------+------------+
                 |                         |
                 v                         v
       cache/resume-working.json  cache/resume-changes.json
                 |
                 v
             Mandatory Factual Audit
                 |
                 v
       Preferred-layout temporary render
                 |
                 v
          Content Fit Feedback
          - overflow: reduce low-value content
          - underfill: add unused high-value evidence
          - fit: continue
                 |
         max three plan revisions
                 |
                 v
          Layout-only Auto-fit
                 |
                 v
     PDF QA + visual QA + publication
```

### Seam placement

The structured files `projection-plan.json` and `projection-language.json` form the seam between the host model and deterministic Python. No provider interface is introduced because the package has no second model adapter and should remain portable across Agent hosts.

The Projection Plan Manager is a deep module: callers supply a workspace and the two model artifacts; the module hides schema validation, evidence-link validation, projection materialization, Manifest generation, fingerprinting, and atomic writes.

## 7. External interface

Planned Python interface:

```python
build_projection(
    workspace: Path,
    plan_path: Path,
    language_path: Path,
) -> BuildResult
```

Planned CLI:

```bash
python3 scripts/projection_plan_manager.py build \
  --workspace "$USER_WORKSPACE" \
  --plan "$USER_WORKSPACE/cache/projection-plan.json" \
  --language "$USER_WORKSPACE/cache/projection-language.json"
```

The interface must:

- read only active `sourced` and `candidate_confirmed` claims;
- validate the current JD and Source Snapshot fingerprints;
- refuse incomplete plans or language artifacts;
- write the Tailored Resume and Tailoring Manifest atomically only after every validation passes;
- return a structured result identifying built paths, clarification state, and validation findings.

Suggested CLI exit semantics:

- `0`: projection and Manifest built successfully;
- `1`: invalid plan, invalid language output, stale input, or evidence violation;
- `2`: clarification is required before a final plan can be built.

## 8. Projection Plan contract

Top-level fields:

```json
{
  "schema_version": 1,
  "revision": 1,
  "status": "ready",
  "target_jd_fingerprint": "sha256:...",
  "source_snapshot_fingerprint": "sha256:...",
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
  "summary_intent": {},
  "experience_plans": [],
  "skills_plan": {},
  "optional_sections": [],
  "next_cuts": []
}
```

### Plan status

- `needs_clarification`: contains one to five questions and cannot be materialized.
- `ready`: has complete evidence links and can proceed to language optimization.
- `revision_required`: previous geometry feedback requires a content revision.

### Experience plan

```json
{
  "entity_id": "experience-microsoft-software-engineer-...",
  "importance": "critical",
  "target_bullet_count": 4,
  "reason": "Carries the strongest P1/P2 AI platform and tool-calling evidence.",
  "content_intents": [
    {
      "intent_id": "intent-ms-mcp-tool-calling",
      "claim_ids": ["claim-mcp", "claim-azure-openai"],
      "capability_ids": ["cap-p1-tool-calling"],
      "operation": "EMPHASIZE",
      "content_intent": "MCP diagnostics workflow using Azure OpenAI tool calling for incident investigation",
      "target_lines": 2
    }
  ]
}
```

`importance` is an explainable model decision, not a numeric fixed score. Allowed values are `critical`, `important`, and `supporting`.

### Optional section decision

```json
{
  "section": "awards",
  "entity_ids": ["award-chinese-patent-..."],
  "decision": "remove",
  "reason": "The patented algorithm remains represented in the selected JD.COM evidence and the standalone section does not cover a target P1/P2 capability."
}
```

## 9. Clarification protocol

The Projection Planner may emit one to five questions only when an answer could change P1/P2 content selection, factual specificity, or module budget.

Questions may target:

- exact tool or platform;
- scale or metric;
- ownership level;
- partner or customer scope;
- production or completion state;
- evaluation method or result.

Questions must not target unsupported P3 terminology solely to increase keyword coverage. Candidate answers are ingested as entity-bound Candidate Confirmations with original excerpts. A final ready plan is generated only after ingestion or an explicit decision to retain the Gap.

## 10. Model-driven content budget

The model decides relative value using the full JD Capability records, Match Types, Evidence States, linked Atomic Claims, recency, uniqueness, and overlap. Python does not maintain a P1/P2/P3 numeric ranking formula.

Hard constraints:

- every formal employment Evidence Entity appears;
- every formal employment entry has one to five bullets;
- no bullet combines claims across different Evidence Entities;
- selected metrics remain attached to their source entity;
- optional sections may be removed;
- Summary, contact, employment chronology, and education remain complete;
- material decisions include a reason suitable for the Tailoring Manifest and final report.

Typical, non-binding model behavior:

- critical experience: three to five bullets;
- important experience: two to three bullets;
- supporting experience: one bullet;
- optional content: include only when it adds distinct target value.

These ranges guide the model. Only the one-to-five employment bounds are deterministic.

## 11. Skills evidence-chain policy

The model generates two to four dynamic Skill Presentation Groups. Category names are target-specific; no fixed category taxonomy is required. Under the preferred readable layout, the Skills body must occupy two to four measured PDF lines, excluding the section heading. A group should normally render on one line; when wrapping pushes the section beyond four lines, Content Fit trims, regroups, or removes lower-value items using actual geometry feedback.

The Tailored Resume evolves the Skills display contract from a comma-delimited string to a list of individually auditable display terms:

```json
{
  "category": "AI Platforms & Tooling",
  "items": ["Azure OpenAI", "MCP", "RAG", "Evals"]
}
```

Readers, validators, and renderers must continue accepting the legacy string form. Legacy input is normalized to a list before planning or auditing. Rendering joins the list with `,` and does not expose evidence metadata in the Tailored Resume.

A Skill item may appear only if at least one condition holds:

1. it directly or semantically supports a P1/P2 JD Capability;
2. it is used by a selected Experience or Project Content Intent;
3. it is a role-foundational capability supported by an active Atomic Claim.

A Skill item should be removed when:

- it is unsupported;
- it is low-value P3 terminology that displaces stronger evidence;
- it duplicates or is strictly contained by another displayed term;
- it is relevant only to removed optional content and adds no independent role value;
- it exists only for keyword repetition.

Each displayed Skill item carries its own claim links and basis:

```json
{
  "display_term": "Azure OpenAI",
  "claim_ids": ["claim-microsoft-azure-openai"],
  "capability_ids": ["cap-p2-llm-api"],
  "basis": "P2 direct and used by a selected MCP diagnostic Content Intent"
}
```

Canonical names and casing are frozen during language optimization. The model may organize, order, deduplicate, and strictly normalize terms, but it may not replace internal authentication with OAuth, a general API with a ChatGPT Plugin, or an evidenced technology with a JD-only technology.

Each `skills[i].items[j]` path receives a normal single-entity Manifest binding to the Evidence Entity that owns its supporting Atomic Claims. A dynamic `skills[i].category` is a presentation label: its Manifest entry uses `binding_mode: "presentation"`, records the grouped item paths and reason, and is not allowed to masquerade as an Evidence Entity. The factual auditor permits this mode only for Skill Presentation Group categories and verifies that any technical term in the category is supported by at least one bound item in that group.

## 12. Resume Language Optimizer

### Responsibility

The Projection Planner decides what to say. The Resume Language Optimizer decides how to say it. It transforms Content Intents into final Summary, bullet, optional-section, and Skills-category display text.

The host model performs the transformation. Python validates the result and never calls an external model.

### Language output contract

```json
{
  "schema_version": 1,
  "plan_revision": 1,
  "target_jd_fingerprint": "sha256:...",
  "items": [
    {
      "intent_id": "intent-ms-mcp-tool-calling",
      "rendered_text": "Built an MCP diagnostic workflow on Azure OpenAI, using tool calling to investigate incidents across GPU telemetry, technical documentation, and SQL data.",
      "source_claim_ids": ["claim-mcp", "claim-azure-openai"],
      "style_actions": [
        "lead_with_specific_system",
        "remove_template_language"
      ],
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

The `meaning_check` is an explanatory self-check. It does not authorize text and cannot replace the factual auditor.

### Resume register

- professional, technical, and restrained;
- implicit first person, with no `I`, `me`, `my`, `we`, or `our` narration;
- no contractions, conversational hooks, humor, fake candidness, chatbot offers, or personal-story voice;
- canonical technical vocabulary preserved;
- one primary contribution per bullet;
- concise evidence-first structure without forcing every bullet into one formula.

### Adopted Humanizer patterns

- remove inflated significance and promotional claims;
- remove empty adverbs and qualifiers;
- replace `serves as`, `stands as`, and `boasts` with direct language;
- avoid negative parallelism such as `not only X, but Y`;
- avoid forced groups of three when the third item adds no evidence;
- remove unsupported trailing `ensuring`, `fostering`, `highlighting`, or similar participial claims;
- remove filler such as `in order to`, `responsible for`, and `it is important to note`;
- avoid synonym cycling that changes technical precision;
- preserve proper nouns, canonical tools, metrics, dates, scope, and ownership.

### Rejected Humanizer patterns

- intentional mistakes, slang, or abnormal grammar;
- detector-evasion scores;
- forced burstiness or sentence-length variance;
- random rare action verbs;
- automatic bans on every em dash, every three-item list, or every isolated stock word;
- blog-style voice injection, first person, jokes, rhetorical questions, or manufactured personality;
- paraphrasing ATS-critical technical terms;
- adding metrics to satisfy an achievement formula.

### Selective rewrite rule

Content Fit revisions must not trigger a whole-resume rewrite. Unchanged `intent_id` records keep identical `rendered_text` unless the revised Projection Plan explicitly changes their space budget or content intent. This limits unrelated wording drift and produces stable diffs.

## 13. Projection materialization and Manifest generation

The Projection Plan Manager combines the current Projection Plan and language output.

For every non-empty Tailored Resume field it must produce exactly one Manifest entry containing:

- `projection_path`;
- `rendered_text`;
- `binding_mode` (`single_entity` by default, `presentation` only for dynamic Skills category labels);
- `entity_id` and active `source_claim_ids` for every `single_entity` entry;
- grouped Skill item paths for a `presentation` category entry;
- operation;
- Match Type;
- declared Semantic Normalizations;
- reason.

Skill items use paths such as `skills[0].items[0]`, so Azure OpenAI, MCP, RAG, and Evals may each bind to the Evidence Entity that actually owns the evidence. The auditor must not relax single-entity binding for any other field type.

Every removed Source Snapshot field or prior projection field must have a removed-entry record. Optional section decisions are not sufficient by themselves; the resulting Manifest must list the exact removed source fields.

The module writes temporary JSON files, validates them, computes fingerprints, and then atomically replaces `resume-working.json` and `resume-changes.json`. Invalid input never partially updates either file.

## 14. Content Fit loop

### Preferred-layout render

Before layout auto-fit, render the Candidate PDF using the project-preferred readable layout. Use actual PDF geometry rather than source character estimates.

Planned geometry feedback:

```json
{
  "schema_version": 1,
  "plan_revision": 1,
  "verdict": "overflow",
  "page_count": 2,
  "bottom_whitespace_mm": 6.2,
  "section_geometry": {
    "summary": {"line_count": 4, "height_mm": 16.1},
    "experience[0]": {"line_count": 11, "height_mm": 47.8},
    "skills": {"line_count": 7, "height_mm": 31.2}
  },
  "sparse_trailing_bullets": ["experience[2].bullets[1]"]
}
```

### Overflow revision order

The model considers, in order:

1. remove low-value optional sections;
2. remove low-value or duplicate Skills;
3. merge overlapping Content Intents within one Evidence Entity;
4. shorten supporting bullets without removing required evidence;
5. reduce supporting employment entries to one bullet;
6. reduce important content only when lower-value options are exhausted.

This order is a model instruction, not a fixed numeric deletion algorithm. The model records each decision and reason.

### Underfill revision order

Before expanding fonts or spacing, the model checks for unused high-value active claims:

1. add a distinct Content Intent to the most relevant Evidence Entity;
2. restore an over-compressed P1/P2 contribution;
3. add a necessary evidence-supported Skill;
4. stop adding when no high-value evidence remains.

Only then may layout auto-fit expand typography and spacing.

### Iteration limit

A maximum of three content revisions is allowed. Every revision reruns plan validation, language validation, materialization, factual audit, temporary rendering, and geometry inspection.

## 15. Layout auto-fit

Existing `auto_fit_layout()` remains layout-only. It may adjust:

- font scale;
- line height;
- section spacing;
- item spacing;
- margins within project safety limits;
- compact mode.

It may not add, remove, merge, reorder, or rewrite content. Content problems reported by PDF QA return to the Content Fit workflow, not the layout tuner.

## 16. Language quality diagnostics

A deterministic AI-pattern linter may be added only as an advisory diagnostic. It must report explainable patterns, not an AI probability.

Possible advisory checks:

- dense stock AI vocabulary;
- repeated bullet syntax;
- negative parallelism;
- forced tricolon;
- unsupported trailing participial clause;
- filler and empty qualifier;
- noun-heavy nominalization;
- vague outcome or unclear causality;
- repeated result across adjacent bullets.

Blocking checks:

- chatbot artifacts;
- unresolved placeholders;
- first-person narration in final resume fields;
- language artifact missing or adding plan intents;
- Manifest text mismatch;
- unknown, inactive, revoked, or cross-entity claims;
- tool, metric, scope, environment, completion-state, or ownership drift;
- removal of required canonical terms for selected capabilities.

An isolated word, em dash, or valid three-item technical list cannot independently block publication.

## 17. Error handling and publication safety

### Planning failure

- Invalid or stale plan: fail without modifying the current projection.
- `needs_clarification`: return questions and do not build.
- Unknown claim or capability link: fail and report the exact intent.

### Language failure

- Missing intent output, extra intent output, changed claim links, or plan revision mismatch: fail.
- Meaning self-check reports a change: fail before materialization.
- Deterministic factual audit detects drift: fail before rendering.

### Content Fit failure

- Three revisions exhausted without acceptable geometry: retain the last Candidate PDF under `rejected/` when available and preserve the current Accepted Resume.
- Underfill with no unused high-value evidence: accept content selection and let layout auto-fit expand within readable limits.

### Publication failure

Existing PDF and visual QA behavior remains authoritative. A failed Candidate never replaces the Accepted Resume.

## 18. Planned code and documentation changes

New files:

- `scripts/projection_plan_manager.py`
- `tests/test_projection_plan_manager.py`
- `docs/research/humanized-resume-language-layer.md`
- `references/projection-planning-protocol.md`

Modified files:

- `SKILL.md`
- `CONTEXT.md`
- `references/resume-working-schema.md`
- `references/prompt-recipes.md`
- `references/execution-checklist.md`
- `references/resume-language-quality.md`
- `scripts/resume_shared.py`
- `scripts/evidence_ledger_manager.py`
- `scripts/audit_factual_integrity.py`
- `scripts/check_content_quality.py`
- `scripts/check_pdf_geometry.py`
- `scripts/generate_quality_report.py`
- `templates/modern_resume_template.py`
- `tests/test_resume_shared.py`
- `tests/test_evidence_ledger.py`
- `tests/test_factual_audit.py`
- `tests/test_content_quality.py`
- `tests/test_pdf_geometry.py`
- `tests/test_pdf_pipeline.py`
- `tests/test_quality_report.py`

`generate_final_resume.py` and `layout_auto_tuner.py` should change only if integration requires passing already-computed artifacts or diagnostics. Their content-mutation boundary must remain unchanged.

## 19. Testing strategy

### Plan validation

- stale JD or Source Snapshot fingerprint fails;
- `needs_clarification` plan cannot build;
- more than five clarification questions fails;
- omitted formal employment entity fails;
- employment with zero or more than five bullets fails;
- fewer than two or more than four Skill Presentation Groups fails;
- legacy comma-delimited Skills input normalizes to item lists without changing display text;
- each `skills[i].items[j]` has an independent single-entity Manifest binding;
- a dynamic Skills category may use presentation binding, but another field type may not;
- fewer than two or more than four measured Skills body lines requires a Content Fit revision;
- optional Awards or Projects may be removed;
- inactive, revoked, unknown, or cross-entity claim fails;
- build failure leaves existing projection and Manifest unchanged.

### Language validation

- exactly one language item exists per Content Intent;
- unknown or duplicate intent fails;
- changed claim links fail;
- numbers, canonical tools, dates, scope, environment, and ownership remain supported;
- first-person, chatbot residue, and placeholders block;
- stock wording and formulaic structures produce advisory findings;
- accurate isolated terms and valid technical lists do not false-positive;
- unchanged intents retain identical text across Content Fit revisions.

### Materialization and audit

- valid fixtures produce a complete Tailored Resume and 100% Manifest coverage;
- removed fields are fully recorded;
- factual audit passes for every valid fixture;
- Semantic Normalizations remain explicit and cannot introduce a tool or scope.

### Geometry feedback

- one-page fit, multi-page overflow, and sparse underfill are identified from actual PDF coordinates;
- section line counts and heights are stable on fixture PDFs;
- sparse trailing bullet findings remain available;
- geometry calculation never relies on source character count.

### End-to-end acceptance fixtures

Use the same candidate with at least two JDs.

OpenAI Plugins fixture:

- Microsoft MCP, Azure OpenAI, tool calling, Evals, developer documentation, RAG, production APIs, and reliability receive priority;
- Skills contain two to four relevant groups;
- standalone Patent/Awards is removed while the JD.COM bullet may retain the `patented` signal;
- every employment entry remains with at least one bullet;
- factual audit, content QA, one-page A4, PDF QA, and visual QA pass.

Distributed Systems fixture:

- Skills shift toward Java, Go, C#, Kafka, Kubernetes, Redis, high availability, and observability;
- TikTok and JD.COM high-throughput evidence receives more space;
- MCP and Evals are reduced when they no longer justify page cost;
- the same publication gates pass.

Model behavior itself is not unit-tested through network calls. Static plan and language fixtures test the contract. Manual end-to-end runs on supported Agent platforms verify that the host model follows the protocol.

## 20. Acceptance criteria

1. The same Candidate Evidence Ledger produces materially different content budgets and Skills for different JDs.
2. Model reasoning, not a fixed keyword score, decides vocabulary, importance, and removal order.
3. Every formal employment entry remains and has one to five bullets.
4. Skills contain two to four dynamic, evidence-supported Skill Presentation Groups, expose individually auditable item paths, and render into two to four measured body lines under the preferred layout.
5. High-value evidence may trigger no more than five Clarifications.
6. Projection planning and language output are independently structured and validated.
7. Resume language is specific, natural, restrained, and free of dense chatbot patterns without using detector-evasion methods.
8. Every Tailored Resume field has a valid Manifest entry and every removal is recorded.
9. Content Fit uses real PDF geometry and runs at most three revisions.
10. Layout auto-fit remains content-neutral.
11. The output is one A4 page with extractable text and readable geometry.
12. Any failure preserves the prior Accepted Resume.

## 21. Research basis

- [`docs/research/humanized-resume-language-layer.md`](../../research/humanized-resume-language-layer.md)
- `blader/humanizer`: <https://github.com/blader/humanizer>
- `shir-danishyar/humanize`: <https://github.com/shir-danishyar/humanize>
- Wikipedia WikiProject AI Cleanup patterns: <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>
- Harvard FAS resume guidance: <https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/>
- Yale OCS resume bullet guidance: <https://ocs.yale.edu/resources/writing-impactful-resume-bullets/>
- Digital.gov Plain Language: <https://digital.gov/guides/plain-language/writing>
- Liang et al., detector bias: <https://doi.org/10.1073/pnas.2302083120>
- Sadasivan et al., detector limitations: <https://arxiv.org/abs/2303.11156>
