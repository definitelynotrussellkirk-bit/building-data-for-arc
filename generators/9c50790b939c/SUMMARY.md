# 9c50790b939c

On a color-7 field, one vertical 8/9 **source rail** has a contiguous color-9 block at its top or bottom. One unique all-8 **target rail** is exactly two cells longer. The transformation clears the source block, then paints `input_nines + 1` cells at the matching end of the target.

Version `3.1.0` generates canonical-scale rail fields rather than singleton noise: every input contains the 2/4/6/8/10 rail-length ladder and 10–15 total vertical runs. Its five public axes are exact and observable (`grid_h`, `grid_w`, `source_length`, `block_position`, `distractor_rails`). It also emits non-half source blocks to refute the strongest canonical-fitting shortcut, “paint exactly half of the target rail.”

Kind: `per_puzzle`. Rule hash: `846ddca6645d`.
Approval is derived by the catalog from current code and retained evidence.
