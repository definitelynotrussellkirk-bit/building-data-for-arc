# Working notes: c1b80aa665e4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-850fa15abd85c458 — native parametric family

- Preserved the exact canonical default as `isolation_policy=all_isolated`.
- Added `largest_cluster_color`: segment nonzero components, retain the unique largest non-singleton component's input-derived color, then recolor only isolated cells of that color to 9.
- Supports 2–6 demonstrations and 1–4 prefix-stable queries with matched inputs across settings; four queries are retained and query 4 is a substantive 30x30 scene.
- Constructive first demonstrations vary component order, anchor position/color, and aggregate color mass. The bounded self-review covered 64 episodes, 320 visible demo prefixes, 19,200 named-rival checks, 64 public projections, and 42 protected-Racket evaluations with no finding.
- Native qualification passed 4/4 jobs (both settings at seeds 0 and 17; 3 demos and 4 queries; 40 protected-Racket labels). The source-bound wrong-intermediate replay substitutes the smallest component's color and changes 15 final cells.
- Finite evidence does not prove universal uniqueness. Production `generator.py`, canonical authority, owner acceptance, and training admission remain unchanged/pending.
