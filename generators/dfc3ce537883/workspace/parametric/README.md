# Native parametric prototype: mirror, then fill the contacted frame

This task-local prototype keeps the approved production generator unchanged.
It exposes two episode-fixed settings over the same deterministic inputs:

- `mirror_only` is the exact canonical Racket program, byte-for-byte.
- `fill_contacted_frame` first performs that mirror. The newly mirrored
  color-2 probe selects the one adjacent hollow color-3/4 frame; the selected
  3x3 frame is filled with color 1 and the selected 4x4 frame with color 5.

The four queries are fixed-count and include a substantive 30x30 scene. The
minimum two demonstrations vary both frame color and frame size so the second
stage is not presented as a fixed-color rewrite. `prototype.py` also exposes the
mirror/intermediate/fill boundary for causal counterfactual evidence.

This is a proposed source-bound adapter. Qualification evidence does not imply
acceptance or training admission.
