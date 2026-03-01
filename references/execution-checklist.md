# Execution Checklist

## Phase A: Initialize
1. Execute `scripts/resume_cache_manager.py reset`.
   - Record result: old cache deleted or no old cache found.
2. Check template resume:
   - Run `template-check`.
   - If exists: run `template-use` to load template into working cache.
   - If not exists: request user to upload resume, execute `template-init`, then `template-use`.
   - Error handling: if `template-use` fails (e.g., corrupted base-resume.json), log the error and re-run `template-init` from the raw resume.

## Phase B: Analyze & Draft

### Step B1: JD Diagnosis
1. Collect JD (text/URL/file) or target direction from user input.
2. Produce P1/P2/P3 tiered diagnosis:
   - If JD exists: diagnose against JD requirements.
   - If JD is absent: diagnose against user-provided direction (e.g., SDE + AI model engineering + Data Platform).
   - P1: Critical requirements
   - P2: Important qualifications
   - P3: Nice-to-haves
3. Produce gap report: matched, transferable, gaps (with improvement strategy for each gap).
4. Persist JD analysis results to `cache/jd-analysis.json` via `scripts/resume_cache_manager.py jd-save --workspace . --input <jd-analysis-file>`. The JSON must contain at minimum:
   - `position`: target position title
   - `keywords`: object with `P1`, `P2`, `P3` arrays
   - `alignment`: object with `matched` and `gaps` arrays
   - Optional: `company`, `source`, `optimization_actions` array

### Step B2: Apply All Modifications
1. Apply optimization decisions using standard action codes (see `references/optimization-actions.md`):
   - `LEAD_WITH`: Reorder sections to front-load P1-matching content
   - `EMPHASIZE`: Rewrite weak bullets using four-element formula
   - `QUANTIFY`: Add measurable metrics to vague descriptions
   - `REWORD`: Replace synonyms with exact JD terminology (P1 first, then P2)
   - `MERGE`: Combine overlapping bullets into stronger single entries
   - `DOWNPLAY`: Remove or reduce low-relevance content
2. Document each action with target path, action code, and reason.
3. Execute `scripts/resume_cache_manager.py update` to persist all changes.

## Phase C: Compress & Quality

### Step C1: Volume Gate

Check `cache/resume-working.json` against volume thresholds.

#### Volume Thresholds (triggers consolidation if any exceeded)
- Total word count: recommended 520-760
- Non-empty lines: recommended 32-52
- Total experience bullets: recommended 8-14
- Single bullet: no more than 2 lines (~28 English words)

#### Consolidation Order (must follow sequence)
1. Delete low-relevance or duplicate information
2. Merge similar bullets
3. Compress sentence structure (keep four elements: action + keyword + method/tool + result)

#### Consolidation Constraints
- Must not fabricate facts.
- Must not delete key qualifications (contact info, core skills, highest relevant experience).
- Must retain JD core keyword matches and quantified results.

After consolidation, execute `scripts/resume_cache_manager.py update`.

### Step C2: QA & De-AI

Run QA checks covering these 4 categories:
1. Structural logic: Summary focus, evidence chain, timeline consistency
2. Natural expression: call `humanizer`
3. Quantified results: check four-element completeness for each experience
4. ATS details: original keyword match, tense consistency, complete contact info

After any QA-driven edits, execute `scripts/resume_cache_manager.py update`.

Note: Always read from `cache/resume-working.json` directly, do not reconstruct from memory.

## Phase D: Generate & Deliver

### Step D1: PDF Generation and Quality Check
1. Call `pdf` skill, then generate PDF.
2. PDF retry strategy (up to 3 attempts if QC fails):
   - Attempt 1: `scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file {name}.pdf --output-dir resume_output --auto-fit`
   - Attempt 2: `scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file {name}.pdf --output-dir resume_output --auto-fit --item-spacing-scale 0.85 --font-size-scale 0.95`
   - Attempt 3: `scripts/generate_final_resume.py --input-json cache/resume-working.json --output-file {name}.pdf --output-dir resume_output --auto-fit --compact`
3. Quality check must cover:
   - A4
   - 1 page
   - Module completeness
   - Text layer extractable
   - No HTML tag leakage
   - Bottom margin 3-8mm
4. If all 3 attempts fail: output the best PDF and note the failed checks in the summary report.

### Step D2: Summary Report
Output the summary report as defined in SKILL.md § Summary Report Format.
Read `cache/jd-analysis.json` for Job Analysis data — do not reconstruct from memory.

### Step D3: Wrap-up
1. Update `cache/user-profile.md` (long-term preference and direction log).
2. Retain `cache/resume-working.json` as baseline for future iterations.
3. Remind user to review contact info and sensitive information (in the report, not as a blocking question).

## Special Scenario Strategies

### Career Transition
- Retain timeline, while prioritizing target-position-relevant capabilities and representative projects.
- Use "transferable skills mapping" to connect original position and target position keywords.

### New Graduate / Early Career
- If insufficient full-time experience, prioritize Education section first.
- Supplement evidence chain with internships, course projects, competitions, open source contributions.

### Executive / Senior Management
- Prioritize strategic impact, organizational upgrades, cross-functional collaboration outcomes.
- Specify team size, budget, revenue growth, profit improvement.
- Information density is very high and may extend to 2 pages if necessary, but must remain ATS-parseable.
