# Install Resume Tailor Agent Setup

Execute the repository setup for `resume-tailor` without cloning any external dependency skills.

## Required Steps

1. Read `docs/guide/installation.md`, especially the `Agent Setup` section.
2. Read `install/agent-install.yaml`.
3. Execute each item in `requirements`, `install_plan`, and `post_check`.
4. Treat `vendor/skills/pdf`, `vendor/skills/docx`, and `vendor/skills/humanizer` as the dependency source of truth.
5. Output a short report that includes environment checks, dependency installation result, and bundled-skill verification result.

## Constraints

- Do not clone or pull upstream skill repositories.
- Do not install `humanizer-zh`.
- Stop and report the first blocking error with an actionable fix.
