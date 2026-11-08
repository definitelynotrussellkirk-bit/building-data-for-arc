# Working notes: 539d4ac45311

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric review 2026-10-25

**Decision.** Keep horizontal completion as the canonical default and add two native settings: vertical completion and an order-sensitive cascade that applies horizontal completion first, then vertical completion to the resulting grid. The cascade is intentionally sequential: the second pass reads cells painted by the first, and the retained protected witness changes when Step A is skipped.

**Repair.** The generator advertised `span_count` through 10 despite only nine nonzero ARC colors and rejected explicit overrides above five. The declared axis is now 1–9, while ordinary random draws retain their prior difficulty bands and explicit overrides may exercise all nine lawful spans.

**Evidence and limit.** Fresh task tests, bounded four-seed audits, protected Racket qualification, causal replay, and single-query privacy projection are retained under `workspace/parametric/evidence/` and `WORK/checks/539d4ac45311/`. This is reviewer-ready evidence, not owner acceptance or training admission. The next useful action is owner integration followed by fresh native qualification and acceptance on the integrated bytes.

