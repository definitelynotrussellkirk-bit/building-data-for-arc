# 4a6d26e0b6ae — proposed generator 3.0.0

Zero-background grids contain separated three-cell horizontal or vertical spans
`(C,0,C)`, using a distinct nonzero color for each motif. Preserve endpoints and
fill each zero center with its endpoint color. The canonical Racket authority is
unchanged; RULE_HASH is `980e1ed5540b`.

Ordinary controls are `grid_h`, `grid_w` (integers 5..14), exact `gap_count`
(1..8 within declared constructive capacity), and helpful `texture`
(`default`, `horizontal`, `vertical`, `edge`). Half the default draws target
canonical-scale support; the other branch varies by difficulty. Stale inert
palette/density/position keys now raise instead of silently doing nothing.

Version 3.0.0 reserves whole spans plus a one-cell Chebyshev moat. Bounded free
placement has an exact-count lattice fallback. Capacity is conservative, not
maximum packing. Distinct-color negative fixtures remain explicit-only and do
not define the normal domain. See notes.md and workspace/README.md.

Kind: `per_puzzle`. Imported version was 2.0.1. This is a reviewer proposal;
catalog approval and training admission remain unverified until maintainer intake.


Round-two validation revision: explicit negatives now require valid geometry and
common metadata; wrong palettes, contradictory blank controls, unknown modes and
falsey malformed metadata are rejected. The sampler and its VERSION remain
unchanged from round one; use the source hash in notes.md for revision identity.
Task-local diagnostic v2 propagates self-check failures, independently checks
requested controls, prioritizes explicit counts and preserves prior evidence.
