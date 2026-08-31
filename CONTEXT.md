# Resume Tailor Domain

The domain language for evidence-based resume tailoring, long-term fact ledger management, and deterministic factual auditing.

## Language

### Core Evidence & Snapshot

**Source Snapshot**:
The immutable structured snapshot extracted directly from the candidate's original base resume.
_Avoid_: Base resume draft, source template, initial working copy

**Candidate Evidence Ledger**:
The durable, cross-JD single source of truth recording all candidate entities, atomic claims, verification states, and provenance.
_Avoid_: Confirmation list, fact database, resume cache

**Candidate Profile**:
The long-term record of candidate global preferences, career positioning, alias preferences, and presentation defaults.
_Avoid_: User settings, config file, preferences cache

**Evidence Entity**:
A bounded structural experience unit (such as a specific company employment, project, education entry, or skill cluster) that anchors atomic claims.
_Avoid_: Resume section, experience item, block

**Atomic Claim**:
The smallest verifiable assertion of responsibility, technical tool usage, quantitative metric, or business outcome bound to an Evidence Entity.
_Avoid_: Bullet point, resume line, fact item

**Provenance**:
The recorded origin and chain of custody of an atomic claim (e.g., extracted from source snapshot, confirmed via targeted user inquiry).
_Avoid_: Source link, citation tag, audit trail

**Candidate Confirmation**:
A factual detail supplied or clarified directly by the candidate during JD-driven questioning.
_Avoid_: User override, prompt answer, user modification

### Capabilities & Alignment

**JD Capability**:
A specific skill, qualification, technical competency, or responsibility demanded by a target Job Description.
_Avoid_: Job keyword, requirement tag, JD bullet

**Match Type**:
The categorical alignment dimension between a JD Capability and candidate evidence (`direct`, `semantic_equivalent`, `transferable`, `gap`).
_Avoid_: Match score, keyword density, fit level

**Evidence State**:
The verification status of an atomic claim or capability (`sourced`, `candidate_confirmed`, `needs_confirmation`, `unsupported`).
_Avoid_: Fact status, validity score, check state

**Clarification**:
A high-leverage targeted inquiry presented to the candidate to confirm missing critical capabilities or metrics.
_Avoid_: Prompt question, interview prompt, gap question

**Gap**:
A target JD Capability for which no supporting evidence exists in the ledger and none was confirmed by the candidate.
_Avoid_: Missing keyword, weakness, disqualifier

**Semantic Normalization**:
The accurate mapping of informal or colloquial technical descriptions to standard industry concepts without expanding scope, ownership, or tools.
_Avoid_: Buzzword injection, keyword stuffing, resume embellishment

### Projections, Manifests & Verification

**Tailored Resume**:
A clean, pure display projection formatted for a specific target JD, completely decoupled from internal ledger IDs.
_Avoid_: Working resume, intermediate output, target draft

**Projection Plan**:
The target-specific, evidence-bound decision record that selects Content Intents, assigns presentation importance, budgets resume space, and decides which optional content to retain, merge, or remove before display text is produced.
_Avoid_: Draft resume, keyword score, layout plan

**Content Intent**:
An evidence-bound instruction describing what a Tailored Resume element must communicate, which Atomic Claims and JD Capabilities support it, and how much presentation space it should receive, without prescribing final prose.
_Avoid_: Bullet draft, prompt fragment, content suggestion

**Resume Language Optimization**:
The meaning-preserving transformation of Content Intents into concise, natural, recruiter-facing resume language while retaining exact evidence scope, canonical technical terms, metrics, and ownership.
_Avoid_: Humanizer bypass, detector evasion, creative rewrite

**Skill Presentation Group**:
A target-specific display grouping whose category label organizes individually evidence-bound Skill items. The label is presentation metadata, not an Evidence Entity or a factual claim about the candidate.
_Avoid_: Skill Evidence Entity, skill claim cluster, fixed skill category

**Content Fit Feedback**:
Measured Candidate PDF geometry describing whether the selected content overflows, underfills, or fits the preferred single-page presentation, used to revise the Projection Plan rather than silently shrink or invent content.
_Avoid_: Character estimate, layout guess, auto-fit score

**Tailoring Manifest**:
The comprehensive change ledger mapping every substantive text element in the Tailored Resume back to its source Atomic Claim IDs and justification.
_Avoid_: Diff file, change log, revision patch

**Audit Finding**:
A deterministic violation identified by the factual auditor or QA rules (e.g., metric fabrication, tool drift, unlinked claim, role inflation).
_Avoid_: Linter error, QA bug, audit warning

**Candidate PDF**:
A freshly compiled PDF undergoing automated factual, content, and geometry quality assurance before publication.
_Avoid_: Staged PDF, temp PDF, draft build

**Accepted Resume**:
A verified, high-quality PDF and matching projection that has passed all factual, content, and layout gates.
_Avoid_: Final output, released resume, master copy
