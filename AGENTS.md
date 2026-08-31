# AGENTS.md

Repository development instructions for the portable `monkey-resume` Skill package.

## Repository Boundary

- Treat this repository as the Skill package, not a personal resume workspace.
- Keep versioned files limited to reusable Skill resources and generic development artifacts.
- Write personal cache and generated PDFs only to the user workspace passed to the scripts.
- Preserve accepted PDFs when a new candidate fails QA.
- Keep `--auto-fit` limited to layout parameters.

## Start Here

1. Read `SKILL.md`.
2. Resolve the repository directory as `MONKEY_RESUME_DIR` and the user's active directory as `USER_WORKSPACE`.
3. Use `scripts/extract_resume_text.py` for PDF, DOCX, Markdown, or text input.
4. Manage candidate facts through `scripts/evidence_ledger_manager.py` and projection cache through `scripts/resume_cache_manager.py`, always with an explicit external workspace.
5. Run `scripts/audit_factual_integrity.py` before rendering. `scripts/generate_final_resume.py` enforces the same audit and requires the manifest, evidence ledger, and Source Snapshot.
6. Read `CONTEXT.md` for domain language and `references/resume-working-schema.md` for data contracts before changing evidence or manifest behavior.

## Development Checks

```bash
python3 -m pip install -r requirements-dev.txt
skills-ref validate .
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```

## Editing Rules

- Use `pathlib.Path` and UTF-8 text I/O.
- Keep imports ordered as standard library, third-party, then local modules.
- Add type annotations to changed functions and use `main() -> int` for CLI entry points.
- Raise descriptive validation or missing-path errors.
- Avoid unrelated formatting.
