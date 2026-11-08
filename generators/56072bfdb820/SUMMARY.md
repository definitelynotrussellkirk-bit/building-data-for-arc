# 56072bfdb820

An 11×11 color-7 field is divided by color-6 lines into a 3×3 meta-grid of
3×3 tiles. Exactly two tiles contain color-2 diamonds. Their ordered relative
placement proposes one color-5 and one color-8 diamond; proposals outside the
meta-grid are clipped, so the lawful result can add zero, one, or two diamonds.
If any input symbol is not color 2, the canonical rule instead returns a 16×16
color-7 grid.

The version 5.0.0 sampler exposes exact `pair_index` (all 36 placements) and
`bad_mask` (none/5/8/both) controls. Its six-position curriculum interleaves a
full two-diamond completion, two clipped completions, and all three contamination
patterns. Every five-demo query rotation refutes the declared canonical-pair,
wrap-instead-of-clip, and “reject only when both bad colors occur” shortcuts.
Default lessons exclude identity/no-op placements; exact overrides retain the
complete lawful placement domain.

Kind: `per_puzzle`. Reviewed version: `5.0.0`.
Canonical authority hash: `5eec51381abd`; the Racket rule behavior was not
changed. Approval remains derived by the catalog from current code and retained
evidence.
