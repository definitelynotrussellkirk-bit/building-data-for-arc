# Working notes: eb150c0ba566

## Current decision

Build the native `prototype_policy` family with `matching` as the byte-exact canonical default and `opposite_shape` as the alternative.  The alternative selects the other header prototype's occupied 3×3 mask for each seed while retaining the seed's paint color, so demonstrations identify a genuine seed-to-mask policy rather than a palette change.

## Source review and repairs

The imported sampler forced each prototype's `(0, 0)` cell to be occupied, which made seed cells monotonically survive every stamp and left the documented seed-erasure behavior untested.  Version 2.2.0 samples the growth origin across all nine prototype cells, accepts canonical zero-at-origin prototypes, calculates seed capacity before generation, and raises on impossible exact `n_seeds` requests instead of silently under-placing them.  Regression tests pin all three repairs.

## Retained evidence

Portable task tests pass 9/9.  Authoring preflight replayed four jobs/four episodes with 32 protected-Racket evaluations while preserving the canonical default.  The source-bound counterfactual witness replays through protected Racket and changes the final footprint when the selected mask is replaced.  A bounded 160-episode audit found no surviving named rival and includes a populated 30×30 case; 16 public one-query projections passed 24 private-field invariance checks and four positive controls.

## Remaining limit and owner action

This is reviewer-ready authoring evidence, not owner acceptance or training admission.  The owner should integrate this exact source and inventory, run fresh native qualification/acceptance, and preserve the canonical default during any reconciliation.
