# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenCode / Claude Code Skill for job-targeted resume optimization. Generates ATS-friendly single-page A4 PDF resumes from a JSON cache, with automated layout tuning and 12-point quality checks. Built on ReportLab for PDF rendering and pdfplumber for quality inspection.

## Commands

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Run all tests
python3 -m pytest -q

# Run single test file
python3 -m pytest tests/test_resume_cache_flow.py -q

# Run single test case
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest::test_base_template_lifecycle -q

# Run tests by keyword
python3 -m pytest -k "layout and not auto" -q

# Core script commands
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-init --workspace . --input raw_resume.txt
python3 scripts/resume_cache_manager.py template-use --workspace .
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit
python3 scripts/check_pdf_quality.py resume_output/resume.pdf
python3 scripts/check_pdf_quality.py resume_output/resume.pdf --json
```

## Architecture

### Data Flow

```
Raw text / DOCX → resume_cache_manager.py → cache/resume-working.json
                                                      ↓
                                          generate_final_resume.py
                                            (+ layout_auto_tuner.py)
                                                      ↓
                                          modern_resume_template.py (ReportLab)
                                                      ↓
                                              resume_output/*.pdf
                                                      ↓
                                            check_pdf_quality.py → PASS / NEED-ADJUSTMENT
```

### Core Scripts (`scripts/`)

| Script | Role |
|--------|------|
| `resume_cache_manager.py` | JSON cache CRUD: reset, init, update, show, diff, template management |
| `generate_final_resume.py` | PDF generation entry point with CLI args; delegates to template + auto-tuner |
| `check_pdf_quality.py` | 12-check PDF QA (page count, A4 size, text layer, margins, sections, contacts, placeholders, etc.) |
| `layout_auto_tuner.py` | Searches 12 preset layout candidates, picks optimal by QA pass + readability score |

### Templates (`templates/`)

| File | Role |
|------|------|
| `modern_resume_template.py` | ReportLab PDF renderer (fonts, styles, section layout) |
| `layout_settings.py` | Immutable dataclass for layout params (font/line/spacing scales, margins); auto-clamps to 0.7–1.3 |

### Stateless Boundary

- **Versioned (skill directory)**: scripts, templates, references, tests
- **Runtime only (not versioned)**: `cache/`, `resume_output/` — isolated per workspace via `.gitignore`

### JSON Cache Schema (`cache/resume-working.json`)

Required fields: `name`, `contact`, `summary`, `skills`, `experience`, `education`
Optional fields: `projects`, `certifications`, `awards`

## Code Style (from AGENTS.md)

- PEP 8, 4-space indent, `from __future__ import annotations` in all scripts
- Type annotations: Python 3.10+ style (`list[str]`, `X | None`), public functions must have return types
- Paths: use `pathlib.Path`, not `os.path`; explicit `encoding="utf-8"` for file I/O
- CLI: `argparse` with `main() -> int` pattern and `raise SystemExit(main())` entry
- Errors: `ValueError` for validation, `FileNotFoundError` with path in message; no broad `except Exception` in core logic
- Imports: stdlib → third-party → local; no wildcard imports
- Tests: one behavior per test, `tempfile.TemporaryDirectory()` for isolation, no network/external dependencies

## Pre-commit Checklist

1. `python3 -m pytest -q` passes
2. Run at least one affected CLI command end-to-end
3. No unrelated large-scale formatting changes
4. Output/cache paths comply with `.gitignore`

## Key Constraints

- **auto-fit** adjusts only layout params (font, line-height, spacing, margins) — never modifies resume content
- Changes to PDF generation logic must be validated against QC check rules
- PDF output must be: single page, A4 (±1mm), text-extractable, ATS-friendly (no table-based layout)
- Backup policy: existing PDFs move to `resume_output/backup/{Position}/` before overwrite

## Dependent Skills

Three external skills required at install time (see `install/agent-install.yaml`):
- `pdf` — PDF read/generate
- `docx` — DOCX resume import
- `humanizer` — AI trace removal

**Claude Code**: Dependencies install to project-local `_deps/skills/`. Run `/install-skill-deps` to auto-install.

**How to use dependent skills in Claude Code**: Claude Code does not auto-discover skills from `_deps/skills/`. When the resume-tailor workflow requires calling a dependent skill (e.g., `pdf`, `docx`, `humanizer`), read the corresponding `SKILL.md` file and follow its instructions:
- `pdf`: Read `_deps/skills/pdf/SKILL.md` before any PDF read/generate action
- `docx`: Read `_deps/skills/docx/SKILL.md` before reading `.docx` files
- `humanizer`: Read `_deps/skills/humanizer/SKILL.md` before AI trace removal
