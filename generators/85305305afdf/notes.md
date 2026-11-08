# Working notes: 85305305afdf

- 2026-10-26: repaired the imported isolated-cell-only generator. The rule is
  run-terminal motion, not “shift every nonzero cell”; ordinary scenes now
  contain both stationary run prefixes and movable terminals, and every
  declared size/count/color boundary is realizable without Boolean cells or
  silent override coercion.
- Added an exact-canonical parametric default and an alternate sequential rule:
  **A** performs the canonical terminal shift; the resulting grid is the
  input-dependent **intermediate**; **B** selects its unique largest same-color
  component and fills that component’s bounding box with color 9.
- The teaching motif is constructed so separate input objects merge only after
  A. A protected-Racket skip-A counterfactual therefore selects a different
  object and output. The largest private query is a substantive 30×30 scene.
- Current reviewer evidence is bounded, not a universal uniqueness proof.
  Owner native qualification/acceptance and training admission remain pending.
