# f29955be8ba2

A one-cell side header encodes a permutation of three equal-height horizontal
blocks. Column 0 rows 0–2 contain `1,2,3` in output order; the remaining header
cells are zero. The output drops column 0 and stacks the three body blocks by
those **top-to-bottom source positions**.

Version `3.0.0` keeps the selected Racket authority unchanged and replaces the
weak v2 sampler with four exact, observable axes: `block_h`, `block_w`,
`permutation`, and `palette_profile`. Ordinary draws use distinct sparse masks,
non-identity permutations, canonical-size/palette anchors, and a three-step
palette schedule. The `varied` profile forces source colors out of ascending
order, refuting the strongest canonical shortcut: treating header values as
ascending foreground-color ranks.

The module includes a structural analyzer, mutation-sensitive `self_check`,
`strict_canonical_like`, exact `observe_overrides`, a Python rule mirror,
executable rivals/witnesses, and a lesson-identifiability hook. Rule pin:
`RULE_HASH = "7f09fab6403a"`.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval remains catalog-owned; this review does not admit training data.
