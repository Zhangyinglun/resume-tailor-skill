# 0002. Silent Conversational Fact Ingestion and Cross-JD Auto-Reuse

## Context
Candidates frequently provide factual details in natural, conversational language during JD-tailoring workflows. Forcing repetitive confirmations on every turn creates friction, while asking the same questions for similar subsequent JDs wastes the candidate's time.

## Decision
1. **Silent Parsing & Ingestion**: The agent parses unstructured candidate responses directly into structured Atomic Claims (binding tools, metrics, role levels, and source provenance) and persists them directly into `candidate-evidence.json` without extra confirmation turns.
2. **Targeted Question Budget**: The agent limits clarification questions to 3–5 high-leverage P1/P2 capability items per JD session.
3. **Cross-JD Semantic Reuse**: Once an atomic claim or capability is confirmed and ingested, semantically equivalent or encompassed requirements in subsequent JDs automatically reuse the existing claim without re-asking the candidate.

## Consequences
- Reduces candidate cognitive load and accelerates subsequent tailoring iterations ("ask once, reuse everywhere").
- Eliminates redundant clarification cycles while continuously enriching the central Evidence Ledger.
