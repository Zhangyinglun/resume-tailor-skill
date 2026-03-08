# resume-tailor

[中文说明](README.zh-CN.md)

`resume-tailor` is a Python-based resume tailoring toolkit plus an agent skill workflow for turning a base resume into an ATS-friendly, single-page A4 PDF.

It combines:

- workspace-local resume cache management
- ReportLab PDF generation
- PDF quality checks
- content quality checks
- layout auto-fit tuning that changes layout only, never resume meaning

## What It Does

- Aligns resume content to a target JD or target role direction
- Maintains a reusable base resume template in `cache/base-resume.json`
- Creates a working copy in `cache/resume-working.json` for each iteration
- Renders a one-page A4 PDF with extractable text
- Runs PDF QA for page size, page count, margins, text layer, placeholders, sections, and contact info
- Supports auto-fit search across layout candidates to recover single-page output without rewriting content
- Archives previously generated PDFs into `resume_output/backup/{Position}/`

## Repository Layout

```text
resume-tailor/
|-- README.md
|-- README.zh-CN.md
|-- SKILL.md
|-- AGENTS.md
|-- scripts/
|   |-- resume_cache_manager.py
|   |-- generate_final_resume.py
|   |-- check_pdf_quality.py
|   |-- check_content_quality.py
|   |-- layout_auto_tuner.py
|   `-- resume_shared.py
|-- templates/
|   |-- modern_resume_template.py
|   |-- layout_settings.py
|   |-- design_tokens.py
|   `-- README.md
|-- references/
|-- tests/
|-- docs/guide/
`-- vendor/skills/
```

## Installation

```bash
python3 -m pip install -r requirements.txt
```

Dependencies are intentionally small:

- `reportlab` for PDF generation
- `pdfplumber` for PDF QA
- `pytest` for test execution

Bundled helper skills already live in `vendor/skills/`:

- `pdf`
- `docx`
- `humanizer`

No separate installation is required for them.

## Quick Start

### 1. Reset working cache

```bash
python3 scripts/resume_cache_manager.py reset
```

### 2. Create a reusable base template from a plain-text resume

```bash
python3 scripts/resume_cache_manager.py template-init --workspace . --input raw_resume.txt
```

Notes:

- `template-init` expects extracted plain text.
- If your source resume is PDF or DOCX, extract/edit it first through the bundled `vendor/skills/pdf` or `vendor/skills/docx` workflow.

### 3. Copy the base template into the working cache

```bash
python3 scripts/resume_cache_manager.py template-use --workspace .
```

This creates:

- `cache/base-resume.json`: long-term baseline
- `cache/resume-working.json`: current working version

### 4. Generate the final PDF

```bash
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output
```

### 5. Generate with auto-fit layout tuning

```bash
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output --auto-fit
```

`--auto-fit` adjusts layout parameters only:

- font size scale
- line height scale
- section spacing scale
- item spacing scale
- page margins

It does not rewrite resume content.

### 6. Run PDF QA

```bash
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf
```

JSON output is also available:

```bash
python3 scripts/check_pdf_quality.py resume_output/02_10_Name_Backend_Engineer_resume.pdf --json
```

## Typical Workflow

For agent-driven use, the intended flow is:

1. Reset old working cache.
2. Check whether `cache/base-resume.json` already exists.
3. If not, initialize it from the user's source resume text.
4. Copy the base template to `cache/resume-working.json`.
5. Analyze the JD and save structured results to `cache/jd-analysis.json`.
6. Update the working cache with targeted content edits.
7. Run content checks and compress to single-page volume targets.
8. Generate the PDF, ideally with `--auto-fit`.
9. Run PDF QA and deliver the final absolute output path.

Related commands:

```bash
# Check template
python3 scripts/resume_cache_manager.py template-check --workspace .

# Show current working cache
python3 scripts/resume_cache_manager.py show --workspace .

# Show template cache
python3 scripts/resume_cache_manager.py template-show --workspace .

# Show JD analysis cache
python3 scripts/resume_cache_manager.py jd-show --workspace .

# Diff working cache against template
python3 scripts/resume_cache_manager.py diff --workspace .

# Update working cache from reviewed JSON
python3 scripts/resume_cache_manager.py update --workspace . --input reviewed_resume.json

# Save JD analysis JSON
python3 scripts/resume_cache_manager.py jd-save --workspace . --input jd_analysis.json
```

## PDF Generation Notes

- Output is fixed to A4 size.
- The template aims for single-page delivery.
- PDF text remains extractable for ATS systems.
- Default font preference is Calibri on Windows, with Helvetica fallback when unavailable.
- When QA passes, old root-level PDFs are archived into `resume_output/backup/{Position}/`.
- When QA fails, previously generated root-level PDFs are removed instead of archived.

## Quality Checks

### PDF QA

`scripts/check_pdf_quality.py` checks:

- page count
- A4 page size
- extractable text layer
- HTML tag leakage
- placeholder content
- top, bottom, and side margins
- section completeness
- contact information
- optional keyword coverage
- layout warnings

### Content QA

`scripts/check_content_quality.py` checks:

- bullet length
- action-verb starts
- quantification ratio
- repeated 3-grams
- experience bullet count

Example:

```bash
python3 scripts/check_content_quality.py cache/resume-working.json
python3 scripts/check_content_quality.py cache/resume-working.json --json
```

## Testing

Use `python3 -m pytest` rather than plain `pytest` to avoid import-path issues.

```bash
python3 -m pytest -q
```

Useful targeted runs:

```bash
python3 -m pytest tests/test_resume_cache_flow.py -q
python3 -m pytest tests/test_resume_cache_flow.py::ResumeCacheFlowTest::test_base_template_lifecycle -q
python3 -m pytest tests/test_generate_final_resume_cli_args.py::GenerateFinalResumeCliArgsTest::test_parse_args_layout_defaults -q
python3 -m pytest -k "layout and not auto" -q
python3 -m pytest --lf -q
```

Optional lint:

```bash
python3 -m ruff check scripts templates tests
```

## Workspace Data and Privacy

This repository is intentionally stateless with respect to user-specific resume data.

Working data should stay in the workspace, not in the repository:

- `cache/`
- `resume_output/`

The repo `.gitignore` already excludes typical runtime data such as:

- `cache/`
- `resume_output/**/*.pdf`
- root-level generated PDFs

## FAQ

### Does auto-fit rewrite resume content?

No. `--auto-fit` only searches layout candidates and adjusts rendering parameters.

### Can I start from PDF or DOCX?

Yes, but the cache manager expects plain text for `init` and `template-init`. Use the bundled `pdf` or `docx` skill flow first, then import the extracted text.

### Where are old PDFs stored?

Older successful outputs are moved to:

```text
resume_output/backup/{Position}/
```

with names like:

```text
02_10_Name_Backend_Engineer_resume_old_1.pdf
```

### Which files are the core entry points?

- `scripts/resume_cache_manager.py`
- `scripts/generate_final_resume.py`
- `scripts/check_pdf_quality.py`
- `scripts/check_content_quality.py`
- `templates/modern_resume_template.py`

## Related Docs

- [SKILL.md](SKILL.md)
- [AGENTS.md](AGENTS.md)
- [templates/README.md](templates/README.md)
- [docs/guide/installation.md](docs/guide/installation.md)
- [references/execution-checklist.md](references/execution-checklist.md)

## License

MIT. See [LICENSE](LICENSE).
