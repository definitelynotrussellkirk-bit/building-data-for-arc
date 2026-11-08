# f563fafba6ac

Generate three or four separated monochromatic objects with 0, 1, or 2
enclosed background regions. Normalize each object to its bounding box, sort by
`(hole_count, color)`, and pack the crops left-to-right with one background
column between neighbours.

Version `3.1.0` pins canonical rule hash `458549b829a3`. The ordinary curriculum
contains executable counterexamples to color-only ordering, input-order tie
breaking, and area-first ordering. Canonical-size anchors retain the linked
`11×15` and `14×15` profiles, while generalized draws vary dimensions and add a
four-object/two-hole branch without allowing the packed output to exceed the
input canvas.

Declared exact axes are `grid_h`, `grid_w`, `n_objects`, and diagnostic list axis
`hole_counts`. All default and override paths record those axes through `GenCtx`;
unknown controls fail loudly. `self_check`, `strict_canonical_like`,
`observe_overrides`, a Python rule mirror, semantic witnesses/rivals, and a
three-demonstration lesson hook are provided.

Kind: `per_puzzle`. Imported version was `2.0.0`; reviewed version is `3.1.0`.
Approval remains a catalog/maintainer decision and is not changed by this review.
