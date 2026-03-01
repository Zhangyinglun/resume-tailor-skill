# Install Resume Tailor Skill Dependencies

Please execute the automatic installation process for resume-tailor dependency skills.

## Required Steps

1. Read and follow the `For LLM Agents` section in `docs/guide/installation.md`.
2. Read `install/agent-install.yaml`, use the **`opencode` platform profile**, and fully execute its `sources`, `install_plan`, and `post_check`.
3. Use `pull-or-clone` strategy for upstream repositories to avoid installation failures when directories already exist.
4. Only install the following skills: `pdf`, `docx`, `humanizer`.
5. Explicitly do not install `humanizer-zh`.
6. Must output installation report (version info, sync method, installation results, post-check results).

## Execution Requirements

- Default to minimal viable approach first, do not modify configurations unrelated to installation.
- Retry once if failure occurs; if still failing, stop and provide actionable fix suggestions.
- Do not claim installation success without completing post-check.
