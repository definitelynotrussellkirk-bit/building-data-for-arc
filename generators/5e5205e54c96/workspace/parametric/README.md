# Native parametric family: nested-frame ring order

`ring_order=outer_to_inner` preserves the exact selected canonical Racket
program byte-for-byte: discover nested color-8 rectangular frames and fill
their interiors from outside to inside using the left-to-right top-row legend.

`ring_order=widest_gap_anchor` is a sequential alternative. Step A sorts the
frames and measures every adjacent inset, deriving the unique widest-gap index.
Step B rotates the legend assignment so the first legend color fills the ring
immediately outside that widest gap. A wrong anchor changes the output, and the
first demonstration deliberately uses a nonzero anchor. Across each episode the
sampler exercises anchors 0, 1, and 2, varied 3/4-frame geometries, boundary
contact, 2-6 demonstrations, exactly four matched private queries, and a
substantive 30x30 case.

The bounded audit checks the competing canonical mode plus fixed-anchor,
narrowest-gap, reversed-order, and single-color shortcuts. It is finite evidence,
not a claim of universal uniqueness.
