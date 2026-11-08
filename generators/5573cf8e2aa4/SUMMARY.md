# 5573cf8e2aa4

A centered full-height maroon(9) divider separates equal left and right panels. The output is a same-size cyan(8) mask of the **occupancy union**: a coordinate is cyan when either corresponding panel cell is nonzero, otherwise it is background(0).

Version `3.0.0` generates 5..9 by 5..9 monochrome panels with explicit blank, left-only, right-only, and occupied-overlap relations. Every third unoverridden sample is an exact canonical-profile 5x11 anchor with red(2) on the left and green(3) or yellow(4) on the right. The other scheduled samples use the same foreground color in both panels, providing a counterexample to the false rule “output cyan wherever the two raw cell values differ.”

Exact axes: `grid_h`, `half_w`, `palette_size`, and `relation_profile`. The generator declares semantic rivals and witnesses, validates canonical inputs, rejects malformed or shortcut-hiding samples, and mirrors rule hash `59a18f0cd9d4` without changing the selected Racket authority.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
