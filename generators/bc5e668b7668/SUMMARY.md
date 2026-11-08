# bc5e668b7668

Pack every column independently: collect its nonzero values from top to bottom,
write them into rows `0..k-1` in the same order, and fill the rest of that
column with zero.

Selected generator version: `3.0.0`. The default distribution uses only the
four canonical height/width profiles `(5,5)`, `(6,6)`, `(6,7)`, and `(7,5)`,
uses the complete palette `0..9`, activates every column, and puts one to three
nonzero values in each column. Easy and hard use disjoint subsets of those
canonical profiles so the difficulty control is observable without leaving the
canonical scale.

A four-slot schedule emits:

1. `canonical_dense`
2. `singleton_witness`
3. `interleaved_order`
4. `canonical_dense`

The singleton branch refutes the strongest canonical-fitting shortcut, “pack
only columns with at least two values.” The interleaved `A-B-A` branch refutes
sorting colors before packing. Exact axes are `grid_h`, `grid_w`, and `texture`;
unknown, ill-typed, and out-of-domain overrides fail loudly, and
`observe_overrides` recovers all three from returned pixels.

The canonical rule is pinned by `RULE_HASH = "bd83e3df4565"`. Outputs remain
Racket-authority derived; the Python generator emits inputs only.

Kind: `per_puzzle`. Approval and training safety remain catalog decisions and
are not changed by this repair.
