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
- **Review Before Export**: Must provide complete review draft and obtain explicit approval before export.
- **Pass Volume Gate Before Review**: Reduce content to target length first, then show full text to user.
- **One Question at a Time**: Only one decision point per round, use `question` tool.
- **ATS Friendly**: No table-based main layout, no images replacing body text, no key info in headers/footers.
- **Fixed A4 + Single Page**: Default delivery 210mm x 297mm, 1 page.
- **PDF Only Delivery**: Final output is PDF only.
- **Call `pdf` skill before PDF actions**: Execute before initial generation, minor regeneration, or final export.

## Stateless Boundary (Mandatory)
- `resume-tailor` skill directory can only store "rules + templates + scripts + references".
- No personalized cache (user preferences, historical JDs, contact info, resume samples) in skill directory.
- Unified directories (relative to workspace):
  - `resume_output/`: Latest PDF
  - `resume_output/backup/`: Historical PDF backups
  - `cache/user-profile.md`: Long-term preference cache
  - `cache/resume-working.md`: Current session resume body

## Minimum Execution Flow
1. **Session Startup Cleanup**: `scripts/resume_cache_manager.py reset`
2. **Read Template Resume**: `template-check` → `template-show` (if not exists, then `template-init`)
3. **JD Diagnosis**: Output P1/P2/P3 matches and gaps, generate initial version after user confirmation
4. **Iterative Updates**: Only change 1 decision point per round, `update` after confirmation
5. **Volume Gate**: First reduce to single-page target, then output full review text
6. **QA + Dehumanization**: Call `humanizer`, complete structure/quantification/ATS checks
7. **PDF Generation and QC**: After user approval, call `pdf` and generate, detect, re-adjust if needed
8. **Wrap-up**: Update profile cache, keep working cache as baseline for future sessions

Complete checklist and thresholds in `references/execution-checklist.md`.

## Fixed Template Baseline (Logical Structure)
Always organize content in the following module order:

```markdown
Header
Summary
Technical Skills
Professional Experience
Education
```

## Script Responsibility Boundaries
- `scripts/resume_cache_manager.py`: Manage `cache/resume-working.md` reset/init/update/show (`cleanup` only manual as needed), and `cache/base-resume.md` template-init/template-use/template-show/template-check.
- `scripts/resume_md_to_json.py`: Convert standardized Markdown to template input JSON.
- `scripts/generate_final_resume.py`: Accept `--input-md` or `--input-json` and generate final PDF.
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

## Reference Materials
- Full process checklist and thresholds: `references/execution-checklist.md`
- ATS strategy: `references/ats-keywords-strategy.md`
- Profile cache template: `references/profile-cache-template.md`
- Working cache structure: `references/resume-working-schema.md`
- Template instructions: `templates/README.md`
