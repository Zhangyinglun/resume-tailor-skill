# Installation Guide

## Requirements

Use Python 3.9 or newer:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/check_agent_platform_support.py
```

The verification command checks Python, `reportlab`, `pdfplumber`, required package files, and whether script entry points work outside the repository directory. It exits nonzero when the baseline fails.

## Agent Setup

- Codex: copy the repository to `$CODEX_HOME/skills/resume-tailor/`, normally `~/.codex/skills/resume-tailor/`.
- Claude Code: open the repository to load `CLAUDE.md`; use a separate personal resume workspace.
- OpenCode: copy the repository to `~/.config/opencode/skills/resume-tailor/`.

No dependency Skills are vendored. PDF generation and text extraction use the open-source Python packages declared in `requirements.txt`.

## Development Validation

```bash
python3 -m pip install -r requirements-dev.txt
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```
