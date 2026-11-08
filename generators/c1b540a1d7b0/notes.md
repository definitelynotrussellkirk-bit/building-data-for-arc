# Working notes: c1b540a1d7b0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/c1b540a1d7b0/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D1 — Native component-scope family (review-2897d39f7102ccb7)

**Decision:** preserve the exact canonical `all_components` Racket program and add `largest_component`, which first identifies the unique largest 4-connected gray component and then applies the canonical arm-versus-room classifier only inside it. The other gray components remain unchanged.

**Why this parameter:** it preserves the source task's object decomposition and local classifier while adding a real input-derived selector. The output mask cannot be produced until the selected component identity is known.

**Teaching contract:** every two-demonstration prefix separates both settings and rejects the declared smallest/first/last/topmost/bottommost and uniform-color rivals. Inputs are matched across settings; demonstrations and queries are independently prefix-stable for 2–6 and 1–4 counts.

**Stress/evidence:** the fourth query is a substantive 30×30 case with multiple components, boundary contact, distractors, and a largest component exceeding 50 occupied cells. Focused staged tests passed (61 tests plus 13 subtests), the 18-case bounded self-audit passed, protected-Racket qualifications passed at 2, 3, and 6 demonstrations (136 evaluations), sixteen one-query public projections passed, and the qualified wrong-intermediate witness was independently replayed.

**Baseline repair:** the pre-existing canonical-fixture test assumed a fixed `__file__.parents` depth and failed in the staged task layout. It now uses `reviewer_support.find_root`, `load_selected_generator`, and `canonical_pairs`.

**Limit:** this is reviewer-ready evidence, not owner acceptance, universal identifiability, or training admission.

Owner reconciliation: Four exact disjoint Racket rules share matched fresh room networks, with natural residual-region maxima varying across demonstrations and queries. This replaces the fixed-six selector proxy. First two demonstrations distinguish all31declared rivals, including fixed-size3/4/6 rules. All prior programs/default and legacy aliases remain intact; the production bitmap audit remains open. Current exact-source acceptance: `evidence/owner-variant-reconciliation/current.json`.
