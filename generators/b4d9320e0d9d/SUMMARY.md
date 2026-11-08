# b4d9320e0d9d — simultaneous diagonal completion

Version `3.0.0`; canonical authority pin `RULE_HASH = "e1a9213544fb"`.

For every **original** 2×2 window, complete the square only when one diagonal
contains the same nonzero colour and both opposite corners are zero. The main-
and anti-diagonal cases are symmetric. Existing cells are never overwritten,
and all decisions use the original input, so additions do not cascade.

The production sampler exposes three exact controls:

- `grid_h`: 7–9
- `grid_w`: 7–10
- `n_pairs`: 2–3 legal diagonal pairs

A deterministic four-slot curriculum covers canonical 7×7/8×8/9×9 profiles
plus a 9×10 width endpoint. Ordinary examples contain both legal orientations
and three lawful near-misses: an occupied opposite corner, a mixed-colour
diagonal, and a same-colour orthogonal pair. Every twentieth sample index at
`index % 20 == 4` is a sparse canonical-scale calibration row; therefore any
four consecutive examples contain at least three fully diagnostic rows.

Executable witnesses and rivals test the main plausible shortcuts, including
one-empty-corner completion, ignored colour equality, orthogonal completion,
and one-orientation-only rules. `lesson_identifiable` checks that no declared
competitor fits every demonstration. The selected Racket rule remains the label
authority; `diagnostic_output` is only a pure test mirror.

Approval remains catalog-owned and is not asserted by this file.
