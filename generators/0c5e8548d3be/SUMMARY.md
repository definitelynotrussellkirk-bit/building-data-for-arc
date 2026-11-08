# 0c5e8548d3be

A 5–8 × 23 input contains four width-5 object panels at columns
`[0..4]`, `[6..10]`, `[12..16]`, and `[18..22]`, separated by blank columns.
Crop each panel to its nonzero bounding box and ignore color. The 4×4 output has
color 8 at `(r,c)` exactly when panel shapes `r` and `c` are equal under a
quarter-turn rotation; otherwise it has 0.

Generator version `3.0.0` exposes three exact observable axes: grid height,
common panel cell count (4–12), and relation partition (2+2, 3+1, or 2+1+1).
Every ordinary sample contains equal-count non-equivalent shapes, a genuine
rotation pair, and a chiral mirror-only pair, so count, exact-shape, reflection,
and color shortcuts all fail within one demonstration.

Kind: `per_puzzle`. Selected authority hash: `c0e3bdee7bdc`.
Approval is derived by the catalog from current code and retained evidence.
