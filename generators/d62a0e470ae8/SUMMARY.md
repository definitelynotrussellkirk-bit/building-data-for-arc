# d62a0e470ae8

A zero-background grid has a transform key at `(0,0)`, one asymmetric main object, and zero to three strictly smaller disconnected objects in the same foreground color. Clear the key, select the unique largest four-connected object, crop its bounding box, then apply key `1` = clockwise quarter-turn, `2` = left-right reflection, `3` = top-bottom reflection, or `4` = half-turn.

The four-example lesson schedule covers all four keys and all four distractor-count residues. Exact observable controls are `grid_profile` (`7x9|8x10|9x9|9x11|10x12|11x13`), `key` (`1..4`), `main_size` (`5..9`), and `n_distractors` (`0..3`). Main shapes have full dihedral orbits, so every selected transform is visible; distractors lie outside the main bounding box and are strictly smaller, making largest-object selection causal.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `43fde3a5fa41`.
Approval is derived by the catalog from current code and retained evidence.
