# resume-tailor

[中文](README.zh-CN.md)

`resume-tailor` is a distributable skill package for Codex, Claude Code, and OpenCode. It turns an existing resume plus a target JD into an ATS-friendly single-page A4 PDF, using bundled scripts, templates, and dependency skills from `vendor/skills/`.

## What It Includes

- JD-oriented resume analysis and rewrite workflow in `SKILL.md`
- Workspace cache management in `scripts/resume_cache_manager.py`
- PDF generation and auto-fit layout tuning in `scripts/generate_final_resume.py`
- PDF and content quality checks in `scripts/check_pdf_quality.py` and `scripts/check_content_quality.py`
- Bundled dependency skills in `vendor/skills/`: `pdf`, `docx`, `humanizer`
- Platform entrypoints for Codex, Claude Code, and OpenCode

## Trigger Examples

Use this skill when the user provides a target JD or direction plus an existing resume and asks for a tailored PDF resume.

```text
I have a Product Manager JD and my current resume. Tailor it into an ATS-friendly single-page PDF.
```

```text
Analyze my resume against this JD, rewrite the content, and generate the final PDF.
```

## Install

```bash
python3 -m pip install -r requirements.txt
```

The repository already bundles its dependency skills. No extra clone is required.

## Platform Entry Points

| Platform | Entry points | Recommended location |
| --- | --- | --- |
| Codex | `SKILL.md`, `AGENTS.md` | `~/.agents/skills/resume-tailor/` |
| Claude Code | `SKILL.md`, `CLAUDE.md`, `.claude/commands/` | repository checkout |
| OpenCode | `SKILL.md`, `.opencode/command/`, `install/agent-install.yaml` | `~/.config/opencode/skills/resume-tailor/` |

Detailed setup notes are in `docs/guide/installation.md`.

## Minimal Workflow

1. Initialize the workspace cache with `scripts/resume_cache_manager.py`.
2. Analyze the JD, update `cache/resume-working.json`, and keep changes factual.
3. Run content and volume checks before PDF generation.
4. Generate the PDF with `scripts/generate_final_resume.py`, optionally using `--auto-fit`.
5. Validate the result with `scripts/check_pdf_quality.py`.

The skill remains stateless. User-specific data stays in workspace runtime folders such as `cache/` and `resume_output/`, not in the skill package itself.

## Core Commands

On Windows PowerShell, prefer `$env:PYTHONPATH='.'; py -3 ...` when calling scripts directly.

```bash
# Reset and inspect cache
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-check --workspace .
python3 scripts/resume_cache_manager.py template-use --workspace .

# Generate and check the final PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit
python3 scripts/check_pdf_quality.py resume_output/resume.pdf

# Smoke-check platform assets
python3 scripts/check_agent_platform_support.py
```

## Repository Layout

```text
resume-tailor/
├── SKILL.md
├── AGENTS.md
├── CLAUDE.md
├── scripts/
├── templates/
├── references/
├── vendor/skills/
├── .claude/commands/
├── .opencode/command/
├── install/
└── docs/guide/
```

## Notes

- `--auto-fit` only changes layout parameters. It does not rewrite resume content.
- The generated PDF targets A4, one page, and extractable text.
- If Calibri is unavailable, the template falls back to Helvetica.
- `references/` contains workflow rules, schema notes, and prompt helpers used by the skill.

## License

MIT. See `LICENSE`.
