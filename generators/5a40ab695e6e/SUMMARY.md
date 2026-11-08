# 5a40ab695e6e

Classify each separated nonzero object by reflection symmetry in its tight
bounding box, then recolor the whole object:

- symmetric left-right **and** up-down → `2`
- symmetric left-right only → `3`
- symmetric up-down only → `4`
- neither symmetry → `6`

The version 3.0.0 sampler is constructive. It places three or four distinct-color
objects in separated corner regions on a `9..14 × 10..16` canvas. The exact
public controls are `grid_h`, `grid_w`, and `n_objects`; all legal joint choices
are observable in the returned grid.

Canonical-scale profiles recur in every difficulty band. A four-profile cycle
`canonical_lr, bbox_trap, canonical_ud, bbox_trap` supplies two non-canonical
shape witnesses per four generated pairs, so every three-demonstration window—and
every three-of-four cyclic query rotation—refutes the strongest canonical-fitting
shortcut: lookup by `(bbox height, bbox width, area)` rather than inspecting the
mask's actual symmetry.

Source colors are selected from `{1,5,7,8,9}`, disjoint from result colors
`{2,3,4,6}`. The canonical Racket authority is unchanged and pinned by
`RULE_HASH = "5e6364f401b5"`.

Kind: `per_puzzle`. Current version: `3.0.0`.
Approval remains a catalog/maintainer decision; this review does not alter it.
