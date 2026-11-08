# Layer-axis parametric family

This native family keeps the source task's per-color bounding-box reflection.
`axis_policy=vertical` is the byte-exact selected canonical program.
`axis_policy=anchor_bbox` adds a real sequential dependency: count every color
and select the unique maximum (`step_a`), derive `lr` versus `ud` from that
anchor's bounding-box aspect (`intermediate`), then flip every color layer using
that one input-derived axis (`step_b`).

The sampler uses four disjoint quadrants. Every layer is asymmetric under both
axes, the anchor count is unique, and both transforms remain inside the layer's
quadrant. The first two demonstrations deliberately use a horizontal anchor in
a tall canvas and a vertical anchor in a wide canvas, rejecting fixed-axis,
overall-aspect, first-color, per-layer-axis, and anchor-only shortcuts. Inputs do
not depend on settings or requested query count. Supported counts are 2–6 demos
and 1–4 queries; the four-query bank ends with a content-rich 30×30 scene.

The adapter is proposed authoring work only. Qualification/preflight and the
separate protected-Racket causal witness do not grant owner acceptance or
training admission.
