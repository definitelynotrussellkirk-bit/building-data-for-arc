# 5bcc776c32fb

Find every color-1 object that is exactly one horizontal row, has odd length,
and has length at least 3. Recolor only that object's middle cell to color 2;
preserve every other cell.

Generator version `3.1.0` uses four exact observable controls (`grid_h`,
`grid_w`, `n_targets`, and `distractor_color`) and a three-profile curriculum.
Across each three-example lesson the profiles supply positive length-9 targets
plus parity, orientation, minimum-size, source-color, and connected-object
negatives. The schedule is designed so any query rotation still leaves the
six declared rival rules refuted by the remaining demonstrations.

Kind: `per_puzzle`. Canonical Racket rule hash: `51414a828017` (unchanged by
this review). Approval is derived by the catalog from current code and retained
evidence.
