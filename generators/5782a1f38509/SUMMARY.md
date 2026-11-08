# 5782a1f38509

Exactly three separated monochromatic 4-connected objects have strictly distinct
occupied-cell areas.  The transformation tightly crops each component, sorts the
crops by occupied-cell count ascending, and top-aligns them left-to-right with
one zero column between adjacent crops.

Version `2.0.0` uses a deterministic five-profile curriculum:
`canonical`, `order_conflict`, `bbox_metric`, `alignment_gap_shape`, and
`shared_color`.  Every five consecutive sample indices contain the full profile
set, including canonical-scale anchors and counterexamples to position, color,
bounding-box, alignment, gapless-packing, rectangle-fill, and color-grouping
shortcuts.

The canonical Racket authority is unchanged and pinned by
`RULE_HASH = "a6b584fba994"`.  The Python mirror and declared rivals are
review diagnostics, not label authority.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval remains catalog-controlled; passing review checks does not itself mark
the generator approved or training-safe.
