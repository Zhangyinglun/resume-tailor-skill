# CLAUDE.md

Repository instructions for Claude Code when this skill package is opened directly.

## Start Here

- Main workflow: `SKILL.md`
- Claude helpers:
  - `.claude/commands/resume-tailor.md`
  - `.claude/commands/check-resume-tailor-setup.md`
- Install notes: `docs/guide/installation.md`

## Core Commands

```bash
python3 -m pip install -r requirements.txt
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-check --workspace .
python3 scripts/resume_cache_manager.py template-use --workspace .
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit
python3 scripts/check_pdf_quality.py resume_output/resume.pdf
python3 scripts/check_agent_platform_support.py
```

## Repository Contract

- This repository is the skill package, not a runtime workspace.
- Keep versioned content limited to reusable scripts, templates, references, and platform entry files.
- User-specific data belongs in `cache/` and `resume_output/` inside the target workspace.
- `--auto-fit` must only change layout parameters.
- Bundled dependency skills live under `vendor/skills/` and are the source of truth.

## Bundled Skills

Read the dependency skill before using that domain:

- `vendor/skills/pdf/SKILL.md`
- `vendor/skills/docx/SKILL.md`
- `vendor/skills/humanizer/SKILL.md`
