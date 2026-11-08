# 2e02ca69563c — Per-Frame Endpoint Routing

Kind: `per_puzzle`. Selected version: `3.0.0`. Rule pin: `024c6f6dd0fa`.

On background 0, recognize complete rectangular frame borders. Inside each frame,
route every color that occurs exactly twice **locally**: from the row-major first
endpoint, move horizontally to the other endpoint's column, then vertically to
its row. Same-row and same-column pairs are valid. Colors with other local
multiplicities stay unchanged. The Racket reference authority has not changed.

The sampler constructs 1–3 separated frames, with 1–2 noncrossing endpoint pairs
per frame and an optional singleton/triple color outside all reserved paths.
Endpoint colors may recur in different frames. Frame palettes include every
nonzero color, including 5; layouts are not restricted to a horizontal row.

Nine controls have exact pixel-observable meanings: `grid_h`, `grid_w`,
`n_frames`, `frame_h`, `frame_w`, `pairs_per_frame`, `frame_color`, `shared_pairs`,
and `n_ignored`. Consult `AXES` for ranges. Unknown/retired controls and impossible
combinations raise explicit errors rather than silently dropping content.

Default consecutive three-example lessons rotate a canonical-scale component,
a broad component, and a contrast component. The contrast refutes the declared
frame-blind, color-8-only, and first-pair-only rivals. This finite guarantee is
for unoverridden consecutive samples, not arbitrary lesson assembly or all
possible alternative rules.

See `notes.md`, `workspace/README.md`, and the task-local tests for rationale,
reproducers, oracle comparisons, and sampler restrictions. Approval remains a
catalog/maintainer decision; local checks do not grant training admission.
