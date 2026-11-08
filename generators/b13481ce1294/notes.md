# Working notes: b13481ce1294

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-850fa15abd85c458 — native parametric family

- Preserved the exact canonical default as `xor_policy=all_exclusive`.
- Added `agreement_color`: align the two panels, retain the unique same-color overlap's input-derived color, then emit only XOR-exclusive cells of that color.
- Supports 2–6 demonstrations and 1–4 prefix-stable queries with matched inputs across settings; four queries are retained. The horizontal two-panel grammar's lawful maximum is 30x29, exercised with substantial content spanning the canvas.
- Constructive first demonstrations vary overlap order and anchor color while exposing anchor exclusives on both sides. The bounded self-review covered 64 episodes, 320 visible demo prefixes, 21,760 named-rival checks, 64 public projections, and 42 protected-Racket evaluations with no finding.
- Native qualification passed 4/4 jobs (both settings at seeds 0 and 17; 3 demos and 4 queries; 40 protected-Racket labels). The source-bound wrong-intermediate replay substitutes the first differing overlap's left color and changes 98 final cells.
- Finite evidence does not prove universal uniqueness. Production `generator.py`, canonical authority, owner acceptance, and training admission remain unchanged/pending.
