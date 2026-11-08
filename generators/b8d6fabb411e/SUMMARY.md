# b8d6fabb411e

Find the one solid color-3 square. For every nonzero/non-3 singleton marker lying
left/right on a square row, or above/below on a square column, paint the gap to
the nearest square edge in that marker's color. Preserve the square, the markers,
and diagonal decoys. Reject conflicting same-side rays that recolor a marker.

Kind: `per_puzzle`. Selected version: `3.1.0`; imported baseline: `3.0.0`.
The reference rule is unchanged (`e88f12aefcff`). The default four-example cycle
now witnesses interior alignment on both axes and retains canonical-size support.

`workspace/alignment_gate.py` is a Racket-backed conditional-coverage probe with
JSON and HTML reports; see its workspace README. Approval is derived separately
by the catalog from current code and retained evidence, not asserted by this review.
