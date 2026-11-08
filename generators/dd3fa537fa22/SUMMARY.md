# dd3fa537fa22

On a zero background, solid non-cyan rectangles are inserts and complete
cyan(8) rectangular perimeters are frames. Render a fresh zero canvas, preserve
only complete frames, and fill a frame's strict interior when an insert has the
same **ordered** `(height, width)` dimensions. Source inserts, unmatched inserts,
and incomplete cyan candidates disappear.

The v3.1.0 teaching distribution has four exact observable profiles: aligned
frames below, crossed frames below, crossed frames above, and a canonical-style
insert-occluded invalid frame candidate. Both crossed profiles use equal-area
transposed dimensions, so every four-demo schedule refutes both horizontal-order
pairing and area-then-horizontal pairing. The canonical authority is pinned by
`RULE_HASH = "4ccb52845749"` and was not changed.

Kind: `per_puzzle`. Reviewed version: `3.1.0`.
Approval remains catalog-derived from current code and retained evidence.
