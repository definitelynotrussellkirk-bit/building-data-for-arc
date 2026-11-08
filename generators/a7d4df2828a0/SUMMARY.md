# a7d4df2828a0 — control-coded local motif transform

Background 0; one control at (0,0): 1=90° clockwise, 2=180°, 3=left/right reflection, 4=up/down reflection. A distinct-color, 4-connected 3–6-cell motif is separated from the control. Transform its normalized coordinates inside its bounding box and paint on a fresh same-size canvas at the original bounding-box origin. Discard the input control. Labels are produced by the unchanged canonical Racket rule.

The version 2.1.0 input sampler reserves both original and transformed extents, so the motif is not truncated. Shapes are generically enumerated connected polyominoes, with at least two rows/columns and a visible selected transform; other symmetries are allowed. Half the defaults in every difficulty retain compact 7–9 grids and four-cell support; the rest use the prior difficulty ranges. All legal canvas-edge placements are eligible.

Declared overrides: grid_h and grid_w in 7..14, motif_size in 3..6, code in 1..4, all valid in every band. Unknown/noninteger/out-of-range overrides are rejected; observe_overrides returns realized values. Four semantic witnesses measure branch coverage, not episode-level identification.

Kind: `per_puzzle`. Current version: `2.1.0`. Rule pin: `089b88c1e5ad`.
Approval remains derived by the catalog from current source and retained evidence; this summary does not grant approval. See notes.md and workspace/README.md for review findings, tests, and the real-Racket conservation probe.
