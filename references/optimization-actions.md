# Optimization Actions

Standard action codes for resume content optimization. Agents MUST use these codes when describing modifications in Phase B.

## Action Codes

| Code | Meaning | When to Use | Example |
|------|---------|-------------|---------|
| `LEAD_WITH` | Move item to the top of its section | Strong match with P1 keywords; most relevant experience | Move AWS bullet to first position in experience |
| `EMPHASIZE` | Rewrite using four-element formula (Action + Keyword + Method/Tool + Result) | Weak or vague bullet that matches a key JD requirement | "Managed servers" → "Reduced server downtime 40% by implementing Kubernetes auto-scaling" |
| `QUANTIFY` | Add or strengthen quantified metrics | Bullet lacks numbers or measurable outcomes | "Improved performance" → "Improved API response time by 65% (800ms → 280ms)" |
| `DOWNPLAY` | Reduce prominence or remove entirely | Low relevance to target position; consumes valuable space | Remove legacy COBOL experience when targeting cloud-native role |
| `MERGE` | Combine multiple items into one stronger bullet | Two or more bullets describe the same achievement/project | Merge "Set up CI pipeline" + "Reduced deploy time" into single bullet |
| `REWORD` | Replace synonyms with exact JD terminology | ATS exact-match optimization; JD uses specific terms | "ML models" → "machine learning pipelines" (matching JD wording) |

## Usage Format

When documenting optimization decisions (in jd-analysis.json or summary report), use this structure:

```
target: experience[0].bullets[2]
action: EMPHASIZE
reason: Bullet matches P1 keyword "distributed systems" but lacks quantification
```

## Combination Rules

- `LEAD_WITH` + `EMPHASIZE`: Move to top AND rewrite — use when the bullet is both highly relevant and poorly written.
- `QUANTIFY` is a subset of `EMPHASIZE` — use `QUANTIFY` when the bullet structure is fine but just needs numbers.
- `DOWNPLAY` + `MERGE`: If two low-relevance bullets exist, merge them first; if still low-value, then downplay.
- `REWORD` can combine with any other action — always apply JD terminology when rewriting.

## Constraints

- All actions MUST comply with the No Fabrication principle.
- `QUANTIFY` must use real numbers from the original resume or reasonable inferences — never invent metrics.
- `DOWNPLAY` must not remove core qualifications, contact info, or highest-relevant experience.
- `MERGE` must preserve all factual claims from both source bullets.
