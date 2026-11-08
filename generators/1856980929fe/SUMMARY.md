# 1856980929fe

A 25–29 by 22–29 black canvas contains one to three separated solid green
rectangles.  Their dimensions are drawn from the six sizes present in the
canonical task: 2×3, 2×4, 2×5, 3×2, 3×3, and 4×2.  Each rectangle is an
independent seed.  At downward level `k`, the rule stamps one copy `k` rectangle
widths to the left and one `k` widths to the right, with vertical spacing equal
to the rectangle height and ordinary clipping at the canvas edge.

Version `3.0.0` replaces the old false/ignored axis surface and degenerate
fixtures with four exact controls (`grid_h`, `grid_w`, `n_seeds`, `rect_size`),
canonical-size support, lower-half and edge-clipped placements, strict structural
validation, and executable rivals/witnesses.  The canonical Racket semantics are
unchanged and pinned by `RULE_HASH = 77504f6c55fa`.

The semantic gate additionally declares the shortcut “expand only the first two
seeds” and a three-seed expansion witness.  A separate proposed
`workspace/parametric/` prototype varies episode-fixed horizontal `fan_stride`
between canonical `1` and nearby variant `2`; it does not change production or
approval status.

Kind: `per_puzzle`. Current version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
