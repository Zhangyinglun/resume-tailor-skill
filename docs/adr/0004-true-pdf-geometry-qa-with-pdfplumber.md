# 0004. True PDF Geometry QA with pdfplumber

## Context
Previous content QA evaluated line-fill and wrap issues using character length heuristics (`len(text) % 95`), which generated false positives and false negatives due to proportional font widths, kerning, and layout margins. Furthermore, rigid metric quotas (requiring numbers in every bullet or 40–60% quantitative ratio) forced unnatural writing.

## Decision
1. We replace character-length heuristics with true PDF layout geometry checks powered by `pdfplumber`, analyzing actual bounding boxes (`bbox`) and word positions across rendered lines to detect orphan words (single words wrapping onto an extra line) and awkward line breaks.
2. We remove the hard requirement for numbers in every bullet and eliminate rigid 40–60% quantitative ratio quotas in favor of natural Action-Context-Result structure scoring.
3. We unify action verb lexicons between `scripts/check_content_quality.py` and `scripts/resume_shared.py`.

## Consequences
- Accurate detection of visual typographic defects in rendered PDFs without spurious character-count warnings.
- Higher quality bullet phrasing that prioritizes substantive engineering achievements over forced numerical metrics.
