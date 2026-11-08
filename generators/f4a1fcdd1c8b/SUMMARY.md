# f4a1fcdd1c8b — border survivors

Treat each same-color 4-connected nonzero component independently. Keep a component unchanged when any cell touches the top, bottom, left, or right grid border; erase components wholly in the interior.

The reviewed generator uses four exact axes (`grid_h`, `grid_w`, `n_border`, `n_interior`), canonical-scale scheduled profiles, executable invariants, Python/Racket parity support, and declared shortcut witnesses. Profiles deliberately include disconnected same-color components with opposite border/interior fates so global color-membership is not a valid shortcut.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `9a57908e9c92`.

Verification: 12/12 inherited battery stages green on final subject `0f46a94fc7d0a9a0`; task regression tests 9/9 green.
