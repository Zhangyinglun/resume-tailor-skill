# 0003. Mandatory Pre-Render Factual Audit Gate

## Context
When tailoring resumes, generative LLMs may inadvertently introduce hallucinations, tool substitutions, role inflation, or ungrounded quantitative metrics. If factual auditing is an optional CLI flag, workflows may skip it.

## Decision
The factual auditor (`scripts/audit_factual_integrity.py`) is enforced as a **mandatory, blocking pre-condition** in `generate_final_resume.py` before any PDF rendering or publication occurs.
- The auditor checks:
  1. Every substantive field in `resume-working.json` is mapped in `resume-changes.json` to valid claims in `candidate-evidence.json`.
  2. Zero metric fabrication: all quantitative numbers must strictly match claims bound to the same entity.
  3. Tool drift prevention: technologies mentioned must be justified by entity tech claims or documented semantic normalizations.
  4. Role integrity: no promotion of contributor roles to ownership/leadership without explicit confirmation.
- Any violation produces an Exit Code 1 error and blocks candidate PDF compilation and acceptance.

## Consequences
- Guarantees zero unverified claims reach the published PDF.
- Forces all tailored modifications to be deterministically grounded in candidate evidence.
