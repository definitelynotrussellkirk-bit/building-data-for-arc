# 50b472d4fc63

A zero-background grid contains isolated vertical occupancy blocks. The canonical authority finds maximal **same-color** vertical runs of length exactly three and recolors only their top and bottom cells to `8`; the middle cell keeps its original color. Same-color runs of length two or four and mixed-color three-cell occupancy blocks remain unchanged.

Generator version `3.2.0` pins canonical `RULE_HASH = "9af5ed1251ca"`. Every default example contains at least one true same-color length-three target and at least one mixed-color length-three negative. Defaults alternate a length-four and a length-two same-color negative, so any three consecutive examples show both exact-length boundaries and any four sequential pairs remain identifiable after rotating any one pair into the query position. Three of every four draws use an exact canonical height/width profile with a two-color foreground; the fourth explores the advertised dimension, palette, and count ranges.

Declared public axes are `grid_h`, `grid_w`, `n_targets`, `n_mixed`, `n_short`, `n_long`, and `palette_size`. All exact overrides are recovered from pixels by `observe_overrides`; unknown, wrong-type, and out-of-range values fail loudly. The task-local semantic contract declares independent witnesses and rivals for the color-blind occupancy shortcut and the two main length-threshold shortcuts.

Reusable probes live in `workspace/reference_probe.py` and `workspace/lesson_probe.py`. The latter checks every query rotation of finite four-pair windows and reads the rival declarations from the current generator rather than copying their names.

Kind: `per_puzzle`. Reviewed version: `3.2.0`.
Approval remains catalog-controlled; this review does not change training admission.
