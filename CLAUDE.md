# CLAUDE.md

Repository instructions for Claude Code when this Skill package is opened directly.

## Workflow

- Read `SKILL.md` first.
- Treat this repository as `RESUME_TAILOR_DIR` and use a separate directory as `USER_WORKSPACE`.
- Run bundled scripts by absolute path and pass `--workspace USER_WORKSPACE` to cache commands.
- Extract PDF and DOCX input with `scripts/extract_resume_text.py`.
- Generate with `scripts/generate_final_resume.py --auto-fit`; publish only when it exits `0`.
- Keep rejected candidates and prior accepted PDFs as described in `SKILL.md`.

## Checks

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_agent_platform_support.py
ruff check scripts templates tests
python3 -m unittest discover -s tests -v
```
