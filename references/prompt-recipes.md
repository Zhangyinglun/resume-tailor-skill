# Prompt Recipes

## 1) JD-Driven Full Auto (Primary Usage)

```text
Here is the JD:
---
{paste JD text here}
---

Generate an optimized single-page A4 ATS-friendly PDF resume targeting this position.
Run the full pipeline automatically: diagnosis, optimization, compression, QA, and PDF generation.
Output a summary report when done.
```

## 2) Direction-Driven Full Auto (No JD)

```text
Generate a general resume targeting: {role} + {specialization areas}.
Example: SDE + AI model engineering + Data Platform + backend systems.

Run the full pipeline automatically and output a summary report when done.
```

## 3) PDF Regeneration Only (Cache Ready)

```text
Regenerate PDF from cache/resume-working.json with auto-fit.
Skip analysis and content modification phases. Run QC and output results.
```

## 4) Manual Edit Then Generate (Resume Phase C+D)

```text
I have manually edited cache/resume-working.json.
Run compression check, QA, humanizer, and then generate PDF.
Output a summary report when done.
```
