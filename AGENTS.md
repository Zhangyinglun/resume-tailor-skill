# AGENTS.md

Codex-facing repository instructions for the distributable `resume-tailor` skill.

## Repository Purpose

This repository is the skill package itself, not a user workspace. Keep only reusable rules, scripts, templates, and bundled dependency skills in versioned files.

The core workflow is:

1. Read `SKILL.md`.
2. Use `scripts/resume_cache_manager.py` to manage workspace cache.
3. Generate the final PDF with `scripts/generate_final_resume.py`.
4. Validate output with `scripts/check_pdf_quality.py`.
5. Read bundled dependency skills from `vendor/skills/` when the workflow requires them.

## Keep These Boundaries

- The skill directory must remain stateless.
- User-specific runtime data belongs in workspace folders such as `cache/` and `resume_output/`.
- `--auto-fit` may change layout parameters only. It must not rewrite resume content.
- PDF output must stay ATS-friendly and single-page A4.
- Use `pathlib.Path` for path handling and `encoding="utf-8"` for text I/O.

## Main Entry Points

- `SKILL.md`: workflow and behavior contract
- `README.md`: package overview
- `CLAUDE.md`: Claude Code instructions
- `.claude/commands/`: Claude helper commands
- `.opencode/command/`: OpenCode helper command
- `install/agent-install.yaml`: OpenCode-style install manifest

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

On Windows PowerShell, prefer `$env:PYTHONPATH='.'; py -3 ...` for direct script calls.

## Editing Rules

- Keep imports ordered as stdlib, third-party, then local modules.
- Add type annotations to new or changed functions.
- Use `argparse` for CLI scripts and `main() -> int` entry points.
- Raise descriptive `ValueError` or `FileNotFoundError` for validation and missing-path failures.
- Avoid unrelated reformatting.

## Recommended Reading Order

1. `README.md`
2. `SKILL.md`
3. `scripts/resume_shared.py`
4. `scripts/resume_cache_manager.py`
5. `scripts/generate_final_resume.py`
6. `scripts/check_pdf_quality.py`
7. `scripts/check_content_quality.py`
8. `templates/design_tokens.py`
9. `templates/modern_resume_template.py`
