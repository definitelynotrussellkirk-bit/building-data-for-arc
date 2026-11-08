# 2a41d6b25262 — normalized template XOR stamp

Implementation version: `3.0.0`. Canonical rule hash: `75fe298a62dd`.

Each input is a 10–18 by 13–22 zero-background grid containing exactly one
4-connected red (`2`) template, one 4-connected green (`3`) template, and one
blue (`1`) anchor. Each template has 3–8 cells and fits a 4×4 box. Normalize
each template independently to its own bounding-box top-left, take the
symmetric difference of the two normalized supports, and stamp those offsets in
cyan (`8`) at the anchor on an otherwise zero output of the same dimensions.
The XOR is **not** normalized or cropped again after the set operation.

The generator enumerates connected polyominoes rather than selecting two fixed
shape pairs. It varies dimensions, geometry, absolute placement, role order,
and anchor location while reserving a complete 4×4 output footprint. The
four-profile schedule covers the three canonical ordered size signatures plus a
leading-offset case. Two residues guarantee an uncropped-origin witness, so a
five-pair lesson remains identifiable when any one pair is rotated into the
query position.

Advertised exact controls are only `grid_h` and `grid_w`; both are validated,
honored, and observable. `strict_canonical_like`, named semantic witnesses,
rivals, canonical shortcuts, and `lesson_identifiable` form the executable
teaching contract. The selected Racket rule and canonical data were not changed.
