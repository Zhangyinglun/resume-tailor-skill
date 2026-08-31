# MonkeyResume

[简体中文](README.zh-CN.md)

**Evidence-grounded resume tailoring with traceable claims and verified PDF delivery.**

MonkeyResume is an open-source Agent Skill that turns a candidate's real experience into a role-specific resume without inventing skills, ownership, metrics, or outcomes. It separates evidence, planning, language, layout, and publication into explicit stages so every substantive resume claim remains reviewable.

## Why MonkeyResume

Most AI resume workflows begin with rewriting and check accuracy afterward. MonkeyResume begins with a durable evidence ledger and blocks publication when a claim cannot be traced back to active evidence.

- **Evidence before wording** — candidate facts live in a cross-JD Evidence Ledger with source excerpts and verification states.
- **JD-aware selection** — requirements are classified as direct, semantically equivalent, transferable, or unsupported before content is drafted.
- **Bounded generation** — the model writes from evidence-bound Content Intents rather than an unconstrained resume prompt.
- **Auditable changes** — a field-level manifest ties substantive output back to claim IDs and explains additions, rewrites, merges, and removals.
- **Protected delivery** — factual, content, PDF, and geometry gates run before a candidate replaces the last accepted resume.

## How It Works

1. **Capture the source** — extract a PDF, DOCX, Markdown, or text resume into an immutable Source Snapshot.
2. **Build the ledger** — normalize experience into entity-bound Atomic Claims and preserve candidate confirmations across job descriptions.
3. **Analyze the role** — map JD Capabilities to evidence, surface genuine gaps, and ask only high-value clarification questions.
4. **Plan and write** — select evidence in a Projection Plan, then produce concise recruiter-facing language without expanding claim scope.
5. **Audit and publish** — verify factual traceability, render the PDF, measure its physical geometry, and publish only after every blocking gate passes.

## Quick Start

MonkeyResume requires Python 3.9 or newer.

The GitHub repository still uses its legacy URL during the rename transition. Clone it into the new local directory name:

```bash
git clone https://github.com/Zhangyinglun/resume-tailor-skill.git ~/Projects/monkey-resume
cd ~/Projects/monkey-resume
python3 -m pip install -r requirements.txt
```

Register the repository in the shared Agent Skills directory:

```bash
mkdir -p ~/.agents/skills
ln -s ~/Projects/monkey-resume ~/.agents/skills/monkey-resume
```

Then provide a resume and a job description or target direction:

```text
Use $monkey-resume to tailor my resume for this role and generate a verified single-page PDF.
```

## Keep Personal Data Outside the Skill

MonkeyResume is a reusable package. Candidate data and generated files belong in a separate user workspace passed explicitly to the scripts.

```text
USER_WORKSPACE/
├── cache/
│   ├── base-resume.json          immutable Source Snapshot
│   ├── candidate-evidence.json   cross-JD Candidate Evidence Ledger
│   ├── candidate-profile.json    long-term presentation preferences
│   ├── jd-analysis.json          dual-axis JD Capability analysis
│   ├── projection-plan.json      evidence-bound content decisions
│   ├── projection-language.json  final language for each Content Intent
│   ├── resume-working.json       current Tailored Resume projection
│   └── resume-changes.json       field-level Tailoring Manifest
└── resume_output/
```

The Skill repository contains reusable runtime resources plus generic documentation, tests, and CI used to maintain them.

## Safety and Quality Gates

- Candidate evidence is the authority; the JD can change emphasis, never history.
- Unsupported requirements stay visible as gaps instead of becoming fabricated resume claims.
- Every substantive projected field must bind to active evidence from a single entity.
- The factual integrity audit runs before rendering and again inside final generation.
- Content revisions are limited and explicit; layout auto-fit changes spacing, margins, and font size only.
- PDFs are built in staging, checked for extractable text and one-page A4 geometry, then published transactionally.
- A failed candidate is preserved under `resume_output/rejected/`; it does not overwrite the last Accepted Resume.
- Visual verification remains a required host-agent step before the final PDF is reported as visually verified.

## Package Layout

```text
SKILL.md                 Agent workflow and publication contract
AGENTS.md                Client-neutral repository development rules
scripts/                 Evidence, projection, audit, and PDF tooling
templates/               ReportLab layout and design tokens
references/              Schemas and conditional workflow guidance
tests/                   Regression and end-to-end tests
```

## Development

Install development dependencies and run the complete validation suite:

```bash
python3 -m pip install -r requirements-dev.txt
skills-ref validate .
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```

See [the installation guide](docs/guide/installation.md) for validator setup and [the domain model](CONTEXT.md) before changing evidence, projection, or manifest behavior.

## License

MIT. Third-party Python packages are installed separately through `requirements.txt` and are not vendored in this repository.
