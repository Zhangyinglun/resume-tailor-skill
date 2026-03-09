# Resume Tailor Workflow

Use this project command when the user wants a job-targeted resume rewrite and PDF delivery inside this repository.

## Steps

1. Read `SKILL.md` and follow the full `resume-tailor` workflow.
2. Read `vendor/skills/docx/SKILL.md` before handling `.docx` input.
3. Read `vendor/skills/pdf/SKILL.md` before any PDF read or generation step.
4. Read `vendor/skills/humanizer/SKILL.md` before de-AI or natural-language polishing.
5. Use commands from `CLAUDE.md` and `AGENTS.md` as the source of truth for install and script execution.

## Required Outcome

- Produce or update `cache/resume-working.json` from the provided resume input.
- Generate a single-page A4 PDF under `resume_output/`.
- Report the full absolute PDF path and summarize optimization decisions.
