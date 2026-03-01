# resume-tailor

[中文](README.zh-CN.md)

An OpenCode / Claude Code Skill for job-targeted resume optimization. Quickly generate ATS-friendly single-page A4 PDF resumes based on target JD.

## Core Capabilities

- **ATS Keyword Alignment**: Automatically extract high-frequency JD keywords and integrate them into resume expressions
- **Job Match Diagnosis**: Analyze matching level between existing experience and target position (P1/P2/P3) and gaps
- **Autonomous Optimization**: Agent autonomously makes all optimization decisions (keyword alignment, content prioritization, compression, layout tuning) and records them in a summary report
- **Smart Content Compression**: Optimize expression and compress to single page without fabricating facts
- **Auto-fit Layout Tuning**: Search 12 preset layout candidates (font/line-height/spacing/margins), pick optimal by QA pass + readability score — never modifies resume content
- **12-Point PDF Quality Check**: Generate A4 PDF with extractable text and auto-check page count, size, margins, sections, contacts, placeholders, etc.
- **AI Trace Removal**: Integrate `humanizer` skill to ensure natural expression and avoid common AI cliches

## Usage Scenarios

This skill automatically activates when you provide the following to OpenCode / Claude Code Agent:

- Target position JD (Job Description)
- Your existing resume (PDF / DOCX / plain text all supported)
- Explicitly request: ATS keyword alignment, job match optimization, compress to single page, or deliver PDF

Typical trigger examples:

```
I have a Product Manager JD and my existing resume, help me optimize it into an ATS-friendly single-page PDF.
```

```
Based on this JD, analyze my resume match level and generate a targeted optimized version.
```

```
Based on my resume, generate a general SDE resume focused on AI model engineering productionization and data platform capabilities.
```

## Installation

For detailed installation steps (both agent auto-install and manual install), see [`docs/guide/installation.md`](docs/guide/installation.md).

### Quick Start

**OpenCode**: Send this message to OpenCode Agent:

```
Please read and strictly execute docs/guide/installation.md to complete resume-tailor dependency skill installation and verification.
```

**Claude Code**: Run the slash command in the project directory:

```
/install-skill-deps
```

## Usage Flow

After skill activation, it automatically executes the following 4-phase flow. Agent autonomously makes all optimization decisions — no manual confirmation needed during execution. A structured summary report is delivered at the end for post-hoc review.

### Phase A: Initialize
- Reset working cache via `resume_cache_manager.py reset`
- Check template resume (`template-check`); if exists, load via `template-use`; if not, run `template-init` with user-provided resume, then `template-use`

### Phase B: Analyze & Draft
- **JD Diagnosis**: Analyze JD (or target direction) and produce P1 (critical) / P2 (important) / P3 (nice-to-have) tier classification with gap report
- **Apply All Modifications**: Apply all optimization decisions in one pass — keyword alignment, description strengthening, content reordering, low-relevance removal — then persist to working cache

### Phase C: Compress & Quality
- **Volume Gate**: Score bullets via `score_all_bullets()` against `cache/jd-analysis.json`, then check working cache against volume thresholds; if exceeded, compress following consolidation order and constraints
- **QA & De-AI**: Call `humanizer` for natural expression, then run structure / quantification / ATS checks

### Phase D: Generate & Deliver
- **PDF Generation**: Call `pdf` skill, then generate with `--auto-fit`. If QC fails, retry up to 3 times with escalating layout parameters
- **Summary Report**: Output a structured summary report covering all decisions made (job analysis, modifications, compression, QA results)
- **Wrap-up**: Update `cache/user-profile.md`, retain working cache for future iterations

**Core Principles**:
- No fabrication (only rewrite, rearrange, compress)
- Autonomous decision making with transparent reporting
- ATS friendly (no table-based layout, no images replacing text)

---

## Data Flow

```
Raw text / DOCX → resume_cache_manager.py → cache/resume-working.json
                                                      |
                                          generate_final_resume.py
                                            (+ layout_auto_tuner.py)
                                                      |
                                          modern_resume_template.py (ReportLab)
                                                      |
                                              resume_output/*.pdf
                                                      |
                                            check_pdf_quality.py → PASS / NEED-ADJUSTMENT
```

## Project Structure

```
resume-tailor/
├── SKILL.md                         # Skill main doc and workflow constraints
├── AGENTS.md                        # Agent coding standards and command reference
├── CLAUDE.md                        # Claude Code project instructions
├── scripts/                         # Core scripts
│   ├── resume_cache_manager.py      # JSON cache CRUD (reset/init/update/show/diff/template-*)
│   ├── generate_final_resume.py     # PDF generation entry point with CLI args
│   ├── check_pdf_quality.py         # 12-check PDF QA
│   ├── check_content_quality.py     # Content-level quality checks (bullet scoring, verb strength)
│   ├── layout_auto_tuner.py         # Search 12 layout presets, pick optimal by QA + readability
│   └── resume_shared.py             # Shared utilities (validation, JSON I/O, parsing)
├── templates/                       # PDF layout templates
│   ├── modern_resume_template.py    # ReportLab PDF renderer (fonts, styles, sections)
│   ├── layout_settings.py           # Immutable dataclass for layout params (auto-clamp 0.7–1.3)
│   ├── design_tokens.py             # Centralized design constants (base font sizes, leading, spacing)
│   └── README.md                    # Template docs
├── references/                      # References
│   ├── execution-checklist.md       # Full process checklist (with volume thresholds)
│   ├── ats-keywords-strategy.md     # ATS strategy
│   ├── prompt-recipes.md            # Prompt templates
│   ├── optimization-actions.md      # Optimization action codes
│   ├── profile-cache-template.md    # User profile cache template
│   └── resume-working-schema.md     # Working cache structure spec
├── tests/                           # Tests
│   ├── test_resume_cache_flow.py    # Cache lifecycle and template management
│   ├── test_output_backup_policy.py # PDF backup policy
│   ├── test_layout_auto_tuner.py    # Auto-fit layout tuning
│   ├── test_layout_settings.py      # Layout param clamping
│   ├── test_layout_integration.py   # Layout integration
│   ├── test_extended_sections.py    # Optional sections (projects, certs, awards)
│   ├── test_cache_diff.py           # Cache diff functionality
│   ├── test_quality_json_output.py  # QA JSON output format
│   ├── test_pdf_margin_checks.py    # PDF margin boundary regression
│   ├── test_content_quality.py      # Content quality checks
│   ├── test_bullet_scoring.py       # Bullet scoring logic
│   ├── test_jd_analysis.py          # JD analysis cache operations
│   ├── test_schema_validation.py    # JSON schema validation
│   └── test_generate_final_resume_cli_args.py  # CLI arg parsing
├── docs/guide/                      # Installation guide
│   └── installation.md              # Agent-executable install flow
├── install/                         # Install manifest
│   └── agent-install.yaml           # Machine-readable install manifest
├── .opencode/command/               # OpenCode commands
│   └── install-skill-deps.md        # Command-based install entry
├── .claude/commands/                # Claude Code commands
│   └── install-skill-deps.md        # Command-based install entry
└── requirements.txt                 # Python dependencies
```

## Development & Testing

### Run Tests

```bash
python3 -m pytest -q
```

### Verify Script Behavior

You can also run tools under `scripts/` individually for debugging:

```bash
# Cache management
python3 scripts/resume_cache_manager.py reset
python3 scripts/resume_cache_manager.py template-init --workspace . --input raw_resume.txt
python3 scripts/resume_cache_manager.py template-use --workspace .

# Generate PDF
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output

# Generate PDF with auto-fit layout tuning
python3 scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file resume.pdf --output-dir resume_output --auto-fit

# QC PDF
python3 scripts/check_pdf_quality.py resume_output/resume.pdf

# QC PDF with JSON report
python3 scripts/check_pdf_quality.py resume_output/resume.pdf --json
```

---

## Technical Notes

### Python Dependencies

- `reportlab`: PDF generation
- `pdfplumber`: PDF quality check
- `pytest`: Test execution

All dependencies maintained in `requirements.txt`.

### Fonts & Cross-Platform

- Template prioritizes Windows **Calibri** font
- If Calibri doesn't exist on system, auto-fallback to **Helvetica** (doesn't affect PDF generation)
- For fixed font effect, recommend installing equivalent font on target system before export

### Cache & Output Directories

Skill directory itself stores no personalized data. All cache and output files are in workspace:

```
Workspace/
├── resume_output/
│   ├── *.pdf                   # Current latest PDF
│   └── backup/                 # Historical PDF backups
└── cache/
    ├── base-resume.json        # Template resume (long-term baseline)
    ├── user-profile.md         # Long-term preference cache
    └── resume-working.json     # Current session resume body
```

---

## Open Source & Contribution

### License

MIT License - See `LICENSE` file

### Privacy & Security

- This repo contains no personal privacy data (contact info, real resume samples, etc.)
- `.gitignore` configured to exclude `cache/` and `resume_output/**/*.pdf`
- Only keep reusable rules, scripts, templates and references

### Contribution Guidelines

Welcome to submit Issues and Pull Requests to improve this Skill!

---

## FAQ

**Q: Why install 3 dependent skills?**

A:
- `pdf`: Read existing PDF resumes and generate final PDF
- `docx`: Read `.docx` format resumes
- `humanizer`: Remove common AI-generated text traces, enhance natural expression

**Q: Can generated PDF be submitted directly?**

A: Yes. Generated PDF auto-runs a 12-point quality check covering:
- A4 size (210mm x 297mm)
- Single page
- Text extractable (supports ATS systems)
- Margin compliance (bottom margin 3–8mm)
- Section completeness and contact info presence
- No HTML tag leakage or placeholder content

**Q: How to customize PDF template style?**

A: Edit `templates/modern_resume_template.py`, a ReportLab-based Python template. Layout parameters (font size, line-height, spacing, margins) are managed in `templates/layout_settings.py`. Design constants live in `templates/design_tokens.py`. See `templates/README.md`.

**Q: Can layout be tuned automatically without rewriting resume content?**

A: Yes. Use `--auto-fit` in `scripts/generate_final_resume.py`. It searches 12 preset layout candidates (font/line-height/spacing/margin scales) and picks the optimal one by QA pass + readability score, keeping JSON content unchanged.

**Q: Will skill save my resume?**

A: No. Skill directory itself is stateless. All cache and output files are in your workspace directory (`resume_output/` and `cache/`), won't commit to Git repo.

---

## Acknowledgments

This skill references the following projects and best practices:

- [Anthropic Skills](https://github.com/anthropics/skills) - `pdf` and `docx` skills
- [blader/humanizer](https://github.com/blader/humanizer) - AI trace removal
- [oh-my-opencode](https://github.com/anomalyco/oh-my-opencode) - Agent auto-install pattern
