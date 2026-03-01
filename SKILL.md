---
name: resume-tailor
description: Use when user provides JD and existing resume, expecting job-targeted optimization, ATS keyword alignment, language polishing, and delivery of a single-page A4 PDF resume.
---

# Resume Tailor Skill

## Core Objectives
- **ATS Hit Rate**: Cover high-frequency JD keywords while maintaining natural expression.
- **Job Relevance**: Prioritize evidence chains and quantified results that best match the position.
- **Delivery Quality**: Output A4 PDF with extractable text and pass format quality checks.

## Inviolable Principles
- **No Fabrication**: Only rewrite, rearrange, compress—no fictional experience/tech/data.
- **Volume Gate Before Generation**: Compress content to single-page target before generating PDF.
- **Autonomous Decision Making**: Agent autonomously makes all optimization decisions (keyword alignment, content prioritization, compression, layout tuning) without asking for confirmation.
- **Transparent Reporting**: All decisions are recorded in the final summary report for user post-hoc review.
- **ATS Friendly**: No table-based main layout, no images replacing body text, no key info in headers/footers.
- **Fixed A4 + Single Page**: Default delivery 210mm x 297mm, 1 page.
- **PDF Only Delivery**: Final output is PDF only.
- **Call `pdf` skill before PDF actions**: Execute before initial generation, minor regeneration, or final export.
- **Auto-fit Scope**: Automatic tuning may adjust layout parameters only; it must not rewrite resume content unless user explicitly asks.

## Stateless Boundary (Mandatory)
- `resume-tailor` skill directory can only store "rules + templates + scripts + references".
- No personalized cache (user preferences, historical JDs, contact info, resume samples) in skill directory.
- Unified directories (relative to workspace):
  - `resume_output/`: Latest PDF
  - `resume_output/backup/`: Historical PDF backups
  - `cache/user-profile.md`: Long-term preference cache
  - `cache/resume-working.json`: Current session resume body
  - `cache/jd-analysis.json`: JD analysis results (keywords, alignment, optimization actions)

## Minimum Execution Flow

### Phase A – Initialize
1. Run `scripts/resume_cache_manager.py reset`.
2. Run `template-check`; if template exists, run `template-use` to load into working cache. If not, run `template-init` with user-provided resume, then `template-use`.

### Phase B – Analyze & Draft
1. **JD Diagnosis**: Analyze JD (or target direction), produce P1/P2/P3 tier classification with gap report, and persist results to `cache/jd-analysis.json` via `jd-save`.
2. **Apply All Modifications**: Apply optimization decisions using standard action codes (`LEAD_WITH`, `EMPHASIZE`, `QUANTIFY`, `DOWNPLAY`, `MERGE`, `REWORD`) as defined in `references/optimization-actions.md`. Document each action with target, code, and reason. Then run `update` to persist.

### Phase C – Compress & Quality
1. **Volume Gate**: Score bullets via `score_all_bullets()` against `cache/jd-analysis.json`, then check working cache against volume thresholds; if compression needed, prioritize removing lowest-scored bullets first, then `update`.
2. **QA & De-AI**: Call `humanizer` for natural expression, then run structure/quantification/ATS checks.

### Phase D – Generate & Deliver
1. **PDF Generation**: Call `pdf` skill, then generate with `--auto-fit`. If QC fails, retry up to 3 times with escalating parameters.
2. **Summary Report**: Output a structured summary report covering all decisions made. **Must include the full absolute path of the generated PDF file.**
3. **Wrap-up**: Update `cache/user-profile.md`, retain working cache.

Complete checklist and thresholds in `references/execution-checklist.md`.

## Summary Report Format

After PDF delivery, output the following report:

```
## Resume Tailor Summary Report

### Job Analysis (from cache/jd-analysis.json)
- Position: {title}
- P1 (Critical): {keywords}
- P2 (Important): {keywords}
- P3 (Nice-to-have): {keywords}
- Matched: {aligned keywords}
- Gaps: {gap keywords with strategies}

### Modifications Applied
- Actions applied: {list of action_code → target, e.g., EMPHASIZE → experience[0].bullets[2]}
- Keywords added: {list}
- Content reordered: {yes/no, brief description}
- Content removed: {list of removed items with reasons}

### Volume & Compression
- Before: {word count} words / {line count} lines / {bullet count} bullets
- After: {word count} words / {line count} lines / {bullet count} bullets
- Compression actions: {list}

### QA Results
- Humanizer: {applied / not needed}
- Structure check: {pass/fail + details}
- ATS keyword coverage: {percentage or list}
- PDF QC: {pass/fail + checks summary}

### Deliverable
- PDF path: {full absolute path of generated PDF}

### Action Required
- Review contact info and sensitive data in the generated PDF.
- {Any failed QC checks or caveats, if applicable}
```

## Fixed Template Baseline (Logical Structure)
Always organize content in the following module order:

```markdown
Header
Summary
Professional Experience
Technical Skills
Education
```

## Script Responsibility Boundaries
- `scripts/resume_cache_manager.py`: Manage `cache/resume-working.json` reset/init/update/show (`cleanup` only manual as needed), `cache/base-resume.json` template-init/template-use/template-show/template-check, and `cache/jd-analysis.json` jd-save/jd-show.
- `scripts/generate_final_resume.py`: Accept `--input-json`, optionally `--auto-fit`, and generate final PDF.
- `scripts/check_pdf_quality.py`: Perform general format and text quality checks.
- `templates/modern_resume_template.py`: Only responsible for PDF layout and export.

## Dependent Skills
- `docx`: Read `.docx` resumes
- `pdf`: Read PDFs, execute all PDF generation and recheck actions
- `humanizer`: Remove AI traces, enhance natural expression

## Agent Installation and Auto-Execution Entry
- Master installation entry: `docs/guide/installation.md`
- Machine-readable manifest: `install/agent-install.yaml`
- OpenCode command entry: `.opencode/command/install-skill-deps.md`
- Claude Code command entry: `.claude/commands/install-skill-deps.md`

## Reference Materials
- Full process checklist and thresholds: `references/execution-checklist.md`
- ATS strategy: `references/ats-keywords-strategy.md`
- Prompt templates: `references/prompt-recipes.md`
- Profile cache template: `references/profile-cache-template.md`
- Working cache structure: `references/resume-working-schema.md`
- Template instructions: `templates/README.md`
- Optimization action codes: `references/optimization-actions.md`
