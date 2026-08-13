---
name: resume-tailor
description: Tailor, review, regenerate, and validate resumes against a job description or target role. Use when the user provides a resume, CV, JD, target direction, or an existing resume-working.json and wants truthful ATS keyword alignment, evidence-based rewriting, content compression, language polishing, or a verified single-page A4 PDF.
---

# Resume Tailor

## Guardrails

- Preserve facts. Rewrite, reorder, merge, or remove content; never invent experience, tools, ownership, dates, or metrics.
- Use quantified results only when the source resume or user supplies the number. Otherwise keep the claim qualitative and record the missing evidence as a clarification item.
- Keep automatic fitting limited to font, spacing, and margins. Never let layout tuning rewrite content.
- Deliver an ATS-readable, extractable-text, single-page A4 PDF.
- Preserve the last accepted PDF whenever a new candidate fails quality checks.

## Resolve Paths First

Set these logical paths before running commands:

- `RESUME_TAILOR_DIR`: the directory containing this `SKILL.md`.
- `USER_WORKSPACE`: the user's active resume workspace, separate from the installed Skill directory.

Run scripts by absolute path from `RESUME_TAILOR_DIR`. Pass `--workspace USER_WORKSPACE` to cache commands. Write personalized data only under `USER_WORKSPACE/cache/` and `USER_WORKSPACE/resume_output/`.

## Workflow

### 1. Initialize Source Data

1. If the user explicitly requests regeneration from an existing `resume-working.json`, keep that cache and skip the remaining initialization steps. Otherwise run `resume_cache_manager.py reset --workspace USER_WORKSPACE`.
2. For `.pdf`, `.docx`, `.txt`, or `.md` input, run `extract_resume_text.py INPUT --output USER_WORKSPACE/cache/source-resume.txt`.
3. Run `template-check --workspace USER_WORKSPACE`.
4. If `cache/base-resume.json` exists, run `template-use --workspace USER_WORKSPACE`. Otherwise run `template-init --workspace USER_WORKSPACE` with the extracted text, then run `template-use` with the same workspace.

### 2. Analyze the Target

1. Analyze the JD or target direction into P1 critical, P2 important, and P3 optional terms.
2. Separate matched evidence, transferable evidence, and unsupported gaps.
3. Save the result through `jd-save` to `cache/jd-analysis.json`.
4. Read `references/ats-keywords-strategy.md` when selecting or placing keywords.

### 3. Tailor Content

1. Apply `LEAD_WITH`, `EMPHASIZE`, `QUANTIFY`, `DOWNPLAY`, `MERGE`, and `REWORD` as defined in `references/optimization-actions.md`.
2. Apply a keyword only where the resume contains supporting evidence.
3. Keep unsupported requirements in the gap report instead of forcing them into the resume.
4. Save the complete JSON with `resume_cache_manager.py update`.

### 4. Compress and Check Language

1. Score bullets against `cache/jd-analysis.json`; remove or merge the lowest-value evidence first when content is too long.
2. Follow `references/execution-checklist.md` for volume thresholds.
3. Read `references/resume-language-quality.md` and remove vague, inflated, or repetitive phrasing without changing responsibility boundaries.
4. Run `check_content_quality.py`. Treat exit code `2` as a warning that requires review, not as a successful quality pass.

### 5. Generate Safely

Run `generate_final_resume.py` with `--auto-fit`, explicit input, and explicit output directory. The generator stages and checks the PDF before publishing it.

- Exit `0`: QA passed; the prior root PDF was archived and the new PDF was published.
- Exit `2`: QA failed; prior PDFs were preserved and the rejected candidate was saved under `resume_output/rejected/`.
- Exit `1`: generation or validation failed.

Revise only the reported issue and retry up to three times. Never delete or overwrite an accepted PDF to make a failing candidate appear successful.

Before delivery, perform visual PDF QA. When the host provides a PDF Skill (Codex: `pdf:pdf`), load and follow it to render and inspect every final page. Otherwise use the fallback in `references/execution-checklist.md`. Do not report the PDF as visually verified unless the rendered pages were actually inspected.

### 6. Report and Retain

1. Run `python -m scripts.generate_quality_report` from `RESUME_TAILOR_DIR`, or run the script by absolute path.
2. Report the absolute PDF path, target role, material content changes, removed content, evidence gaps, content warnings, programmatic PDF QA verdict, and visual PDF QA verdict.
3. Retain `cache/base-resume.json`, `cache/resume-working.json`, and `cache/user-profile.md` for later iterations.

## Output Structure

Use this stable ATS order:

```text
Header
Summary
Professional Experience
Projects (when relevant)
Technical Skills
Certifications or Awards (when relevant)
Education
```

## References

- `references/execution-checklist.md`: commands, thresholds, retry rules, and special cases.
- `references/ats-keywords-strategy.md`: evidence-based keyword selection and matching.
- `references/optimization-actions.md`: modification action codes.
- `references/resume-language-quality.md`: concise resume-specific language checks.
- `references/resume-working-schema.md`: working JSON schema.
- `references/profile-cache-template.md`: optional preference cache structure.
- `references/prompt-recipes.md`: example invocation prompts.
