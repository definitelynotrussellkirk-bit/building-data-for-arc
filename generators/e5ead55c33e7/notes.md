# Working notes: e5ead55c33e7

## 2026-10-26 review

- The base generator was left unchanged. Added an episode-fixed `packing_order` family: exact-canonical `front_first` versus `rear_first`, with identical inputs and the same clear/slide/commit mechanics.
- Sequential dependency: A extracts movable components and produces an input-dependent order from their bounding boxes; B consumes that list one object at a time, committing landed cells into the obstacle set seen by later row-overlapping objects. A protected wrong-order witness changes the final output.
- Self-review found and repaired two sampler defects. First, independently randomized gaps could consume the reserved pre-wall column (seed 0 query 0). Second, some selected four-object shape sets needed more mandatory width than the coarse scene range supplied (seed 6 training item 1). Gap extras are now budgeted, and canvas width is derived from the exact selected shapes, mandatory gaps, and clear pre-wall column.
- Inputs vary colors, shape sequence, bands, canvas dimensions, and horizontal signatures; two demonstrations expose the setting; every episode retains four queries; query four is a dense three-band 30×30 stress case. A 128-seed sweep passed 4,096 labeled pairs for this family after the repairs.
- The final changed-target suite passes 13 tests. The protected probe passes 92 labels across both settings, 2/3/6 demos, and seeds 0/17. Authoring preflight passes all five canonical labels plus 24 parametric labels. Sixteen one-query public views and 24 private-field invariance mutations pass.
- Owner source review, native qualification, and acceptance remain pending; this return grants no training admission.
