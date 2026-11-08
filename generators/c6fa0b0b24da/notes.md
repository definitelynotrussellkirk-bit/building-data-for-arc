# Working notes: c6fa0b0b24da

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 base repair and native parametric review

- Repaired the base generator: strict typed controls, honest observable axes, deterministic local RNG, disjoint palettes, a Python rule mirror, and portable task-local tests. The exact canonical bounding-box fill program remains the default.
- Added `fill_finish=largest_new_region_to_8`: construct the canonical solid bounding box, identify four-connected regions of cells newly created relative to the input, then recolor the unique largest new region to 8.
- Added an executable wrong-order counterfactual whose pre-fill recoloring is erased by the later fill, plus finite-rival teaching checks, matched settings inputs, stable prefixes, four private queries, and a 30x30 two-boundary stress case.
- Two demonstrations uniquely identify both supported settings in the declared finite program family.
- Authoring preflight, protected causal replay, and public projection checks passed. This is reviewer-ready repaired source, not owner acceptance or training admission.
