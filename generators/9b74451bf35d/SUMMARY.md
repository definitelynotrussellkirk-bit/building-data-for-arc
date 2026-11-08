# 9b74451bf35d

Read the fixed 3x11 input as three 3x3 panels A, B, C separated by all-zero columns 3 and 7. A and C use the same source color; B uses a different target color. Infer the unique geometric transform that maps A's occupied-cell support to B's support from the canonical family {identity, rotate-90-CW, rotate-180, flip-left/right, flip-up/down}. Apply that transform to C's support and paint every occupied output cell with B's target color. Ordinary generated lessons schedule only the four non-identity branches and use asymmetric masks so the transform is unambiguous and shortcut-rebutting.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
