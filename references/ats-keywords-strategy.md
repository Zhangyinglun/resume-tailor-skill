# Evidence-Based ATS Keyword Strategy

ATS implementations differ. Treat keyword coverage as a diagnostic aid, not a guaranteed score.

## Extract Terms

Prioritize:

1. Target role and seniority.
2. Explicit required skills and responsibilities.
3. Repeated domain, platform, and delivery terms.
4. Preferred qualifications that the resume already supports.

Without a JD, derive terms from the target role, specialization, and system context supplied by the user.

## Apply the Evidence Gate

For every term, classify it as:

- `matched`: directly supported by the resume.
- `transferable`: supported by adjacent evidence and can be described without changing the fact.
- `gap`: unsupported and must not be inserted as experience.

Use exact JD wording only when it truthfully describes the candidate's work. Keep unsupported terms in the gap report.

## Place Terms Naturally

- Skills: list tools and technologies the candidate actually used.
- Experience and projects: demonstrate terms through sourced actions and outcomes.
- Summary: include only the most important role and capability terms.
- Education and certifications: reproduce actual credentials accurately.

Do not repeat a term solely to raise a count. Prefer evidence in one strong bullet over unsupported repetition across sections.

## Matching Rules

- Use boundary-aware phrase matching so short terms such as `AI`, `R`, and `Go` do not match parts of unrelated words.
- Preserve punctuation in technical terms such as `C++`, `C#`, `.NET`, and `Node.js`.
- Treat common aliases as separate evidence only when the source supports both forms.
- Review every automated hit manually when the term is ambiguous.

## Bullet Pattern

Use this pattern when all elements are supported:

```text
Action + system or capability + method or tool + result
```

Omit a missing element rather than inventing it. A specific qualitative result is better than an unsupported number.

## ATS-Safe Format

- Use a single-column reading order with standard section names.
- Keep contact information in the page body.
- Use extractable text and standard fonts.
- Avoid images as text, decorative skill ratings, and key information in headers or footers.
- Verify the extracted text order from the final PDF.
