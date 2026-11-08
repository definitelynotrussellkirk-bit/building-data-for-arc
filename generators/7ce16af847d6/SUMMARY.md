# 7ce16af847d6

On a zero background, recolor only four-connected blue (`1`) components that
contain exactly nine cells in a `3×3` bounding box.  The generator keeps every
input at a canonical `11×11` or `12×12`, four-color profile and schedules three
scene types over every three consecutive sample indices:

1. `canonical_mix`: two or three solid blue `3×3` targets, three canonical-like
   blue near-misses, and two differently colored decorations.
2. `shape_counterexamples`: adds a hollow blue `3×3`, a nine-cell non-square,
   and a solid `3×3` with a tail.  These distinguish bbox-only, size-only, and
   contains-a-`3×3` shortcuts.
3. `color_counterexample`: adds a solid nonblue `3×3`, distinguishing a
   color-agnostic exact-square shortcut.

The selected Racket rule is unchanged and pinned by `RULE_HASH=a7803abc6931`.
`workspace/reference_probe.py` is an independent Python oracle and cyclic
lesson-schedule census for future reviewers.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
