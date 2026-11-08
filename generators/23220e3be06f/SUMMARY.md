# 23220e3be06f — command-selected motif transform

A zero-background grid contains a command in the upper-left corner and one small two-color motif elsewhere. Erase the command, tightly crop the remaining nonzero motif, then apply command `1` = identity, `2` = clockwise 90°, `3` = 180°, `4` = counter-clockwise 90°, `5` = left-right reflection, or `6` = up-down reflection. The output is the transformed crop.

Generator version: `3.1.0`. Canonical rule hash: `710976311dfe` (authority unchanged).

Ordinary inputs use 7–10 rows, 8–11 columns, 4–8 motif cells, exactly two motif colors, and fully D4-asymmetric support/color patterns so all six commands are observable. The profile schedule includes every exact canonical `(height, width, palette-size)` profile in every difficulty band and also exercises nearby scales. `palette_mode=overlap` lets one motif color equal the command; `distinct` keeps both motif colors different from it.

The five exact axes—`grid_h`, `grid_w`, `code`, `n_cells`, and `palette_mode`—are validated, observable, and jointly supported. Default four-pair production windows use a paired `A,B,A,B` command schedule, so any one held-out pair still leaves the query command demonstrated. The semantic contract declares the canonical-fitting `rotations_only` shortcut and requires flip-command evidence when that rival would otherwise survive.

`tests/test_generator.py` contains 46 source-bound regression tests. `workspace/reference_probe.py` independently checks canonical compatibility, distribution support, determinism, asymmetry, override behavior, and optional Racket parity.
