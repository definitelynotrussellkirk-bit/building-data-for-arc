# Native parametric family

`anchor_policy=bottom_right` is the byte-exact canonical rule. In
`anchor_policy=key_count_corner`, a unique connected color-3 key object has
one through four cells, selecting the motif's top-left, top-right,
bottom-left, or bottom-right corner respectively.

Sequential dependency: **A** counts the key cells and produces the selected
motif-corner record; **B** consumes that corner to calculate offsets and stamp
the motif at the color-1 marker. `always_bottom_right.rkt` is the protected
wrong-intermediate counterfactual.
