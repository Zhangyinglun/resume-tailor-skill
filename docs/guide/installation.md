# Installation Guide

## Python Dependencies

```bash
python3 -m pip install -r requirements.txt
```

On Windows, use `py -3` if `python3` is unavailable. For direct script calls in PowerShell, prefer `$env:PYTHONPATH='.'; py -3 ...`.

## Bundled Skills

This package already includes its dependency skills under `vendor/skills/`:

- `vendor/skills/pdf/SKILL.md`
- `vendor/skills/docx/SKILL.md`
- `vendor/skills/humanizer/SKILL.md`

Do not clone external copies of those skills for this repository layout.

## Agent Setup

Use the repository itself as the canonical `resume-tailor` skill package.

### Codex

- Repo mode: open the repository and let Codex read `AGENTS.md`.
- Skill mode: place this repository at `~/.agents/skills/resume-tailor/`.

### Claude Code

- Open the repository checkout directly.
- Claude-specific instructions live in `CLAUDE.md`.
- Helper commands live in `.claude/commands/`.

### OpenCode

- Preferred location: `~/.config/opencode/skills/resume-tailor/`
- Helper command: `.opencode/command/install-skill-deps.md`
- Install manifest: `install/agent-install.yaml`

## Smoke Check

Run the package smoke check after installation:

```bash
python3 scripts/check_agent_platform_support.py
```

That script verifies required entry files, bundled dependency skills, and basic command availability without relying on repository test files.
