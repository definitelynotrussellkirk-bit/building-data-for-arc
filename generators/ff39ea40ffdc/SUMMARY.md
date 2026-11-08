# ff39ea40ffdc

0-bg grid (size varies) with: (a) TOP-LEFT CONTROL at (0, 0) — a SIZE RANK in {1=smallest, 2=middle, 3=largest}; (b) TOP-RIGHT CONTROL at (0, w-1) — a TRANSFORM in {4=identity, 5=mirror, 6=rotate-CW}; (c) THREE candidate objects, each a RANDOM polyomino of a DISTINCT size, in a shuffled size->color assignment over {7, 8, 9}, scattered at random positions. Rule: read the rank, pick that size-ranked 7/8/9 object, crop it tight, apply the transform from the top-right control, and OUTPUT the transformed crop in the object's color (other objects and controls discarded).

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
