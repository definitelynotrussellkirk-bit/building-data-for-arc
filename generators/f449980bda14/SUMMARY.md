# f449980bda14

0-bg grid (possibly NON-SQUARE) with: (a) 1-3 SOLID color-5 (gray) squares (2x2 to 4x4) at well-separated positions; (b) 4-10 colored DOT cells (each a singleton in some non-{0, 5} color) scattered, each at least 2 cells away from any gray square perimeter. Rule: process dots in reading order. For each dot, find the gray square at minimum L1 distance from its row/col axis. Compute target = one cell outside the square along the dot's axis (clamped to dot's row/col). Place the dot at target on a fresh canvas keeping gray squares.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
