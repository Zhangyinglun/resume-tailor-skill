# Resume Template - Modern Design

## Overview

`modern_resume_template.py` is the default PDF template for resume-tailor, aiming to:
- A4 single-page output
- ATS-friendly (text extractable, linear structure)
- Compact and readable (9.5pt body text)

## Design Features

- Font: Prioritize Calibri, auto-fallback to Helvetica if unavailable
- Header: Name and contact info centered display
- Structure: Summary → Technical Skills → Professional Experience → Education
- Experience section: First line Company (left) and Dates (right); second line Title | Location

## Cross-platform Font Notes

- On Windows, Calibri font files will be prioritized from `C:/Windows/Fonts/`.
- On macOS/Linux or environments without Calibri installed, will auto-fallback to Helvetica.
- Fallback will not block generation process, but different platform font widths may cause slight variations in line count.

## Page and Layout Parameters

- Page: A4 (210mm x 297mm)
- Margins: Top 5mm, Bottom 5mm, Left/Right 0.6in
- Font size: Body 9.5pt, Section headers 10.5pt, Name 15pt
- Line spacing: Body 11pt

## Generation Methods

### Method 1: Markdown Working Cache (Recommended)

```bash
py -3 scripts/generate_final_resume.py --input-md cache/resume-working.md --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output
```

### Method 2: JSON Data

```bash
py -3 scripts/generate_final_resume.py --input-json resume_content.json --output-file 02_10_Name_Backend_Engineer_resume.pdf --output-dir resume_output
```

## Working Cache Related Scripts

### Long-term Template Management (New)

**One-time initialization of long-term template** (first use or updating general resume):

```bash
py -3 scripts/resume_cache_manager.py template-init --workspace . --input my_full_resume.txt
```

**Check if template exists**:

```bash
py -3 scripts/resume_cache_manager.py template-check --workspace .
```

**View template content**:

```bash
py -3 scripts/resume_cache_manager.py template-show --workspace .
```

**Generate initial resume based on JD (simplified workflow)**:

```text
Step 1: Read full `cache/base-resume.md`
Step 2: Model generates initial `cache/resume-working.md` based on JD
Step 3: Continuously update `cache/resume-working.md` based on Q&A
```

### Temporary Working Cache Management

- Initialize cache:

```bash
py -3 scripts/resume_cache_manager.py init --workspace . --input raw_resume.txt
```

- Update cache:

```bash
py -3 scripts/resume_cache_manager.py update --workspace . --input reviewed_resume.md
```

- Cleanup cache (optional, manual trigger):

```bash
py -3 scripts/resume_cache_manager.py cleanup --workspace .
```

## Backup Strategy

Before each new resume generation, existing PDFs in `resume_output/` root directory will be automatically moved to:

`resume_output/backup/{Position}/{name}_old_N.pdf`

Where `{Position}` is inferred from filename `{MM}_{DD}_{Name}_{Position}_resume.pdf`, `{name}` uses original filename (without `.pdf`). Therefore, after generation completes, `resume_output/` root directory always contains only the latest resume.

## Maintenance Recommendations

If content overflows to second page, adjust in the following order:
1. Space after paragraph
2. Bullet spacing
3. Line spacing
4. Margins
5. Font size (not lower than 9.5pt)
