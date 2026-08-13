# Execution Checklist

## Setup

1. Resolve `RESUME_TAILOR_DIR` from the directory containing `SKILL.md`.
2. Resolve `USER_WORKSPACE` from the user's active resume workspace.
3. Run every bundled script by absolute path. Keep all personalized files under `USER_WORKSPACE`.
4. Run `check_agent_platform_support.py` after installation. Stop if its baseline status fails.

## Initialize

1. Run `resume_cache_manager.py reset --workspace USER_WORKSPACE`.
2. Extract `.pdf`, `.docx`, `.txt`, or `.md` input with `extract_resume_text.py`.
3. Run `template-check --workspace USER_WORKSPACE`.
4. Use the existing base template, or initialize it from extracted text and then run `template-use`.

`reset` may remove the current working resume and JD analysis. It must not remove the base resume or user profile.

## Analyze and Tailor

1. Build P1, P2, and P3 keyword tiers from the JD or target direction.
2. Save `position`, `keywords`, and `alignment` through `jd-save`.
3. Record matched evidence, transferable evidence, and unsupported gaps separately.
4. Apply modification action codes from `optimization-actions.md`.
5. Never infer metrics. Ask for the number, keep the result qualitative, or retain it as a gap.
6. Save the complete resume JSON through `update`.

## Volume and Content Quality

Use these as review targets, not universal pass/fail rules:

- 520–760 English words.
- 32–52 non-empty rendered lines.
- 8–14 experience bullets for an experienced technical resume.
- Prefer bullets no longer than about 28 English words.
- Avoid a wrapped final line that contains only a few words.

Compress in this order: remove low-relevance duplication, merge overlapping evidence, then shorten sentence structure. Preserve core qualifications and sourced results.

Run `check_content_quality.py`. Exit `2` means warnings remain and must be reviewed in context.

## Generate and Validate

1. Generate with `generate_final_resume.py --auto-fit`.
2. Treat A4 size, one page, extractable text, required sections, safe minimum margins, complete contact information, and absence of placeholders as hard checks.
3. Treat excessive whitespace and other aesthetic balance findings as warnings.
4. If exit code is `2`, inspect the candidate under `resume_output/rejected/`, adjust the reported issue, and retry up to three times.
5. If all attempts fail, keep the prior accepted PDF and report the rejected candidate path. Do not publish a failed candidate as the latest resume.

After programmatic QA passes, complete visual QA before delivery:

1. When the host exposes a PDF Skill, load and follow it. In Codex, use `pdf:pdf` to render the final PDF and inspect every page.
2. Otherwise, if Poppler is available, render every page with `pdftoppm -png FINAL_PDF OUTPUT_PREFIX`.
3. Keep rendered intermediates under `USER_WORKSPACE/cache/pdf-visual-qa/` or an OS temporary directory, never under `RESUME_TAILOR_DIR`.
4. Inspect for clipped or overlapping text, unreadable glyphs, black squares, inconsistent spacing, weak hierarchy, and unbalanced margins or whitespace.
5. Regenerate and re-render after any material correction. The latest render must have no visual defects before delivery.
6. If neither a PDF Skill nor a render-and-inspect path is available, report programmatic QA separately and mark visual QA as incomplete. Never describe an uninspected PDF as visually verified.

## Report

Read `cache/jd-analysis.json`, `cache/resume-working.json`, and the generated quality report directly. Report the target, applied actions, removed content, unsupported gaps, warnings, programmatic QA verdict, visual QA verdict, and absolute PDF path.

## Special Cases

- Career transition: map only evidenced transferable skills; do not disguise the original role.
- Early career: emphasize relevant projects and education inside the stable template order; do not fabricate professional experience.
- Senior leadership: prioritize organization, scope, and business impact. Keep one page unless the user explicitly requests a two-page variant; the default checker validates one page.
