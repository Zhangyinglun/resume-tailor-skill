# resume-working.json Structure Specification

Working cache file path: `cache/resume-working.json`

Description:
- This file is the "single source of truth for current resume content".
- All iterative modifications, QA previews, and final exports are based on this file.
- Clear old cache on session startup; retain current cache after generation for future iterations.

## Fixed Structure

```json
{
  "name": "FULL NAME",
  "contact": "City, State | Phone | Email | LinkedIn",
  "summary": "Summary sentence 1. Summary sentence 2.",
  "skills": [
    {"category": "Programming Languages", "items": "Python, Go, Java"},
    {"category": "Cloud & DevOps", "items": "AWS, Kubernetes"}
  ],
  "experience": [
    {
      "company": "Company",
      "title": "Title",
      "location": "Location",
      "dates": "Dates",
      "bullets": ["Bullet 1", "Bullet 2"]
    }
  ],
  "education": [
    {"school": "School", "degree": "Degree", "dates": "Dates"}
  ],
  "projects": [
    {
      "name": "Project",
      "tech": "Python, FastAPI",
      "dates": "2024",
      "bullets": ["Project bullet"]
    }
  ],
  "certifications": [
    {"name": "Certification", "issuer": "Issuer", "dates": "2024"}
  ],
  "awards": [
    {"name": "Award", "organization": "Organization", "dates": "2024"}
  ]
}
```

## Constraints

- Required keys:
  - `name`
  - `contact`
  - `summary`
  - `skills`
  - `experience`
  - `education`
- `skills` uses `[{"category": "...", "items": "..."}]` structure.
- `experience` uses company/title/location/dates/bullets structure.
- `education` uses school/degree/dates structure.
- Optional keys: `projects`, `certifications`, `awards`.
- Do not insert analysis text unrelated to resume in cache file.
