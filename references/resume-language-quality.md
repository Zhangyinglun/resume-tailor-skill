# Resume Language Quality

Use this guide during Resume Language Optimization and deterministic content quality checks.

---

## 1. Meaning-Preservation Contract

Language optimization transforms Content Intents into concise, professional, recruiter-facing prose. It MUST preserve exact semantic fidelity to the underlying active claims:

- **Responsibility & Ownership**: Keep the exact responsibility level. Never convert assisting, monitoring, or analyzing into leading, architecting, or owning.
- **Scope & Scale**: Keep system, team, user base, and traffic scope exactly as supported by the claim.
- **Metrics**: Numbers and quantitative claims must originate verbatim from the same Evidence Entity. Never invent, extrapolate, or migrate numbers.
- **Tools & Environments**: Retain canonical names and versions. Do not substitute technologies (e.g. do not replace PostgreSQL with ClickHouse).
- **Production & Completion Status**: Do not upgrade prototypes, internal proofs of concept, or planned work into production deployments.

Every language item must pass the `meaning_check`:
```json
{
  "facts_added": [],
  "facts_removed": [],
  "metrics_changed": [],
  "ownership_changed": false
}
```

---

## 2. Technical Resume Register

Professional technical resumes require a restrained, evidence-first register:

- **Perspective**: Use implicit first/third person typical of resume bullets. Never use explicit first-person pronouns (`I`, `me`, `my`, `we`, `our`).
- **Tone**: Technical, concise, and objective. Avoid promotional hype, inflated descriptors (`visionary`, `world-class`), and conversational colloquialisms.
- **Structure**: Lead with a strong, specific action verb and the technical system/method, followed by concrete outcome or purpose. Avoid robotic identical sentence structures across adjacent bullets.
- **Standard Vocabulary**: Preserve canonical technical terms (e.g., `Azure OpenAI`, `Kubernetes`, `GraphQL`, `CI/CD`).

---

## 3. Humanizer Pattern Adaptation

Resume language optimization borrows select principles from plain-language and anti-AI-pattern research, adapted strictly for technical resumes:

### Adopted Patterns (Encouraged)

- **Eliminate Promotional Fluff**: Remove empty marketing adjectives (`revolutionary`, `seamless`, `cutting-edge`, `pioneering`).
- **Strip Verbal Clutter**: Remove filler phrases like `responsible for`, `served as`, `in order to`, `successfully`, `played a key role in`.
- **Avoid Negative Parallelism**: Replace contorted constructions like `not only X but also Y` with direct conjunctions or separate clauses.
- **Prune Unevidenced Participles**: Cut trailing participial clauses that state generic platitudes without evidence (e.g., `, ensuring maximum efficiency and fostering team synergy`).
- **Break Forced Tricolons**: Do not force lists into artificial sets of three when two items are accurate and the third is redundant filler.
- **Direct Voice**: Replace passive nominalizations (`facilitated the implementation of`) with direct active verbs (`implemented`).

### Rejected Patterns (Forbidden)

- **Detector-Evasion Hacks**: Never inject artificial typos, grammatical errors, slang, unnatural sentence fragmentation, or forced perplexity/burstiness to evade third-party AI detectors.
- **Synonym Cycling**: Do not substitute standard industry terminology with rare or archaic synonyms.
- **Conversational Voice**: Do not inject personal storytelling, conversational intros, jokes, rhetorical questions, or chatbot-style assistance offers.
- **Invented Metrics**: Never fabricate numbers or KPIs simply to satisfy formulaic bullet templates (e.g. Google XYZ formula).
- **Blanket Punctuation Bans**: Do not ban standard em dashes, colons, or technical lists when used correctly.

---

## 4. Quality Diagnostics: Advisory vs. Blocking

### Blocking Quality Checks (Halt Build / Publication)

The following issues are deterministic failures that block projection compilation or PDF publication:

1. **Chatbot Conversational Residue**: Phrasing such as *"Certainly! Here is the revised resume"*, *"I hope this helps"*, or *"Let me know if you need anything else"*.
2. **Unresolved Placeholders**: Bracketed or template markers like `[Insert metric]`, `[Company Name]`, `[TBD]`, or HTML comments `<!-- TODO -->`.
3. **First-Person Pronouns**: Explicit occurrences of `I`, `me`, `my`, `mine`, `we`, `our`, `ours`.
4. **Intent Mismatch**: Language output containing missing, extra, or duplicated `intent_id` entries relative to the Projection Plan.
5. **Claim Drift**: Language output referencing different or inactive claim IDs.
6. **Wording Drift on Unchanged Intents**: Revising the text of an `intent_id` across Content Fit revisions when its intent, claims, and line budget were unchanged.

### Advisory Pattern Diagnostics (Review Warnings)

The following patterns trigger advisory warnings in `check_content_quality.py`. They indicate opportunities for model polish but do not automatically halt publication unless accompanied by factual or layout defects:

- **Stock AI Vocabulary Clusters**: Dense concentrations of cliché buzzwords (`leverage`, `spearhead`, `harness`, `streamline`, `testament`).
- **Repetitive Bullet Syntax**: Three or more consecutive bullets starting with identical grammatical patterns.
- **Forced Parallelisms**: Heavy negative parallelism or artificial tricolons.
- **Vague Outcomes**: Bullets ending in ungrounded claims like *"significantly enhancing performance"* without specific metrics or concrete qualitative mechanisms.
- **Bullet Density**: Less than 3 or more than 6 bullets on a substantive experience entry.

---

## 5. Semantic Normalization Rules

Automatic semantic normalization is permitted ONLY when the candidate's active claims strictly entail the target term without expanding scope:

- *Valid*: "Built document embedding retrieval system prior to LLM response" $\rightarrow$ declared normalization to "RAG".
- *Invalid*: "Experience with relational databases (MySQL)" $\rightarrow$ rewriting as "Distributed Spanner database".
- *Invalid*: "Scripted deployment automation" $\rightarrow$ rewriting as "Kubernetes platform engineering".

Every semantic normalization must be declared in the Tailoring Manifest with its supporting basis.
