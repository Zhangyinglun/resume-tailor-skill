# resume-working.md Structure Specification

Working cache file path: `cache/resume-working.md`

Description:
- This file is the "single source of truth for current resume content".
- All iterative modifications, QA previews, and final exports are based on this file.
- Clear old cache on session startup; retain current cache after generation for future iterations.

## Fixed Structure

```markdown
# HEADER
Name: FULL NAME
Contact: City, State | Phone | Email | LinkedIn

## SUMMARY
Summary sentence 1. Summary sentence 2.

## TECHNICAL SKILLS
- Programming Languages: Python, Go, Java
- Cloud & DevOps: AWS, Kubernetes

## PROFESSIONAL EXPERIENCE
### Company | Title | Location | Dates
- Bullet 1
- Bullet 2

## EDUCATION
- School | Degree | Dates
```

## Constraints

- Headers must be the following 5 blocks:
  - `# HEADER`
  - `## SUMMARY`
  - `## TECHNICAL SKILLS`
  - `## PROFESSIONAL EXPERIENCE`
  - `## EDUCATION`
- Experience uses level-3 heading `###` to indicate individual experience entries.
- Education uses `- School | Degree | Dates` single-line structure.
- Skills uses `- Category: items` structure.
- Do not insert analysis text unrelated to resume in cache file.
