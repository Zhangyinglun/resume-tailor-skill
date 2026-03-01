# Install Resume Tailor Skill Dependencies (Claude Code)

Please execute the automatic installation process for resume-tailor dependency skills.

## Required Steps

1. Read and follow the `For LLM Agents` section in `docs/guide/installation.md`.
2. Read `install/agent-install.yaml`, and use the **`claude-code` platform profile** (`skills_dir = ./_deps/skills`).
3. Fully execute `sources`, `install_plan`, and `post_check` with paths resolved under `_deps/skills/`.
4. Use `pull-or-clone` strategy for upstream repositories to avoid installation failures when directories already exist.
5. Only install the following skills: `pdf`, `docx`, `humanizer`.
6. Explicitly do not install `humanizer-zh`.
7. Must output installation report (version info, platform profile, sync method, installation results, post-check results).

## Post-check

Verify the following files exist:

- `_deps/skills/pdf/SKILL.md`
- `_deps/skills/docx/SKILL.md`
- `_deps/skills/humanizer/SKILL.md`

## Execution Requirements

- Default to minimal viable approach first, do not modify configurations unrelated to installation.
- Retry once if failure occurs; if still failing, stop and provide actionable fix suggestions.
- Do not claim installation success without completing post-check.
