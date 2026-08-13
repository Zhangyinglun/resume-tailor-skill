# AGENTS.md

Codex-facing instructions for the distributable `resume-tailor` Skill package.

## Repository Boundary

- Treat this repository as the Skill package, not a personal resume workspace.
- Keep versioned files limited to reusable rules, scripts, templates, references, metadata, and tests.
- Write personal cache and generated PDFs only to the user workspace passed to the scripts.
- Preserve accepted PDFs when a new candidate fails QA.
- Keep `--auto-fit` limited to layout parameters.

## Start Here

1. Read `SKILL.md`.
2. Resolve the repository directory as `RESUME_TAILOR_DIR` and the user's active directory as `USER_WORKSPACE`.
3. Use `scripts/extract_resume_text.py` for PDF, DOCX, Markdown, or text input.
4. Manage cache through `scripts/resume_cache_manager.py` with an explicit `--workspace`.
5. Generate through `scripts/generate_final_resume.py` and validate through the quality scripts.

## Development Checks

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_agent_platform_support.py
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```

## Editing Rules

- Use `pathlib.Path` and UTF-8 text I/O.
- Keep imports ordered as standard library, third-party, then local modules.
- Add type annotations to changed functions and use `main() -> int` for CLI entry points.
- Raise descriptive validation or missing-path errors.
- Avoid unrelated formatting.
