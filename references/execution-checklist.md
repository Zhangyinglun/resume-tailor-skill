# Execution Checklist

## Phase 0: Session Startup
- Execute `scripts/resume_cache_manager.py reset`.
- Record result: old cache deleted or no old cache found.

## Phase 1: Input Collection and Diagnosis
1. Check template resume:
   - Run `template-check`
   - If not exists, request user to upload resume and execute `template-init`
   - Run `template-show` to read full template
2. Collect JD (text/URL/file, required).
3. Output P1/P2/P3 tiered diagnosis:
   - P1: Critical requirements
   - P2: Important qualifications
   - P3: Nice-to-haves
4. Output gap report: matched, transferable, gaps (provide brief improvement suggestions for each gap).
5. Let user confirm diagnosis conclusion before proceeding to initial version generation.

## Phase 2: Iterative Negotiation
- Only suggest 1 item per round, wait for confirmation before the next.
- Suggestion priority:
  1. Fill missing core keywords
  2. Strengthen descriptions with JD original words
  3. Adjust content order (relevant content first)
  4. Remove low-relevance content
- After each round of confirmation, execute `scripts/resume_cache_manager.py update`.

## Phase 3: Pre-Review Volume Gate

Before outputting "Resume Full Preview", must check `cache/resume-working.md`.

### Volume Thresholds (triggers consolidation if any exceeded)
- Total word count: recommended 520-760
- Non-empty lines: recommended 32-52
- Total experience bullets: recommended 8-14
- Single bullet: no more than 2 lines (~28 English words)

### Consolidation Order (must follow sequence)
1. Delete low-relevance or duplicate information
2. Merge similar bullets
3. Compress sentence structure (keep four elements: action + keyword + method/tool + result)

### Consolidation Constraints
- Must not fabricate facts.
- Must not delete key qualifications (contact info, core skills, highest relevant experience).
- Must retain JD core keyword matches and quantified results.

### Review Draft Attached Information
- Original volume
- Current volume
- Deletion/merge summary
- Retained keywords list

## Phase 4: QA and De-AI

Before layout, output QA report covering these 4 categories:
1. Structural logic: Summary focus, evidence chain, timeline consistency
2. Natural expression: call `humanizer`
3. Quantified results: check four-element completeness for each experience
4. ATS details: original keyword match, tense consistency, complete contact info

Note: When outputting "Resume Full Preview", read directly from `cache/resume-working.md`, do not reconstruct from memory.

## Phase 5: PDF Generation and Quality Check
1. Generate only after user explicitly approves full text.
2. Call `pdf` skill first, then generate PDF.
3. Priority command:
   - `scripts/generate_final_resume.py --input-md cache/resume-working.md --output-file ... --output-dir resume_output`
4. Quality check must cover:
   - A4
   - 1 page
   - Module completeness
   - Text layer extractable
   - No HTML tag leakage
   - Bottom margin 3-8mm
5. If not passing, fine-tune and regenerate until passing.

## Phase 6: Wrap-up
1. Update `cache/user-profile.md` (long-term preference and direction log).
2. Retain `cache/resume-working.md` as baseline for future iterations.
3. Provide extended suggestions only when user requests (interview points, cover letter opening, gap addressing).
4. Remind user to review contact info and sensitive information.

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
