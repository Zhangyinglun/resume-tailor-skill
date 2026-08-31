# Optimization Actions

Use these action codes in the Tailoring Manifest. Every action remains bound to active Atomic Claim IDs.

| Code | Meaning | Use |
|---|---|---|
| `KEEP` | Preserve sourced display text | The source already presents the evidence well |
| `LEAD_WITH` | Move an item earlier | Strong P1/P2 relevance |
| `EMPHASIZE` | Strengthen structure or specificity | Evidence is relevant but understated |
| `QUANTIFY` | Add a sourced metric | The same Evidence Entity contains the exact metric claim |
| `DOWNPLAY` | Reduce prominence | Low relevance consumes space |
| `MERGE` | Combine overlapping evidence | All component claim IDs remain linked |
| `REWORD` | Use accurate JD terminology | Direct or strictly entailed semantic normalization |
| `REMOVE` | Omit an item from the projection | Evidence is valid but not useful for this target |
| `REORDER` | Change section/item ordering | Ordering improves target relevance without changing facts |

## Manifest Record

```text
projection_path: experience[0].bullets[2]
operation: EMPHASIZE
source_claim_ids: [claim-123, claim-456]
entity_id: experience-acme-engineer
match_type: direct
reason: Leads with the P1 distributed-systems capability.
```

Array paths identify the current projection location only. Claim IDs and Entity IDs provide durable factual identity.

## Constraints

- `QUANTIFY` uses exact candidate-supplied or source-snapshot values from the same Evidence Entity.
- `REWORD` cannot introduce a new tool, scope, metric, ownership level, environment, production status, or completion state.
- `MERGE` preserves all factual boundaries and links every supporting claim.
- `DOWNPLAY` and `REMOVE` cannot remove essential contact information or misstate chronology.
- Project display names may change as a presentation preference while project nature remains unchanged.
