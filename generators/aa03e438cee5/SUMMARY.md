# aa03e438cee5

0-bg grid (h~8-10, w~8-12) with 2-4 SINGLETON SEED CELLS at scattered positions with Manhattan distance > 2 between any pair (so radius-1 diamond footprints don't overlap). Each seed in a random color from {1..9}. Rule (EXPAND EACH SEED INTO RADIUS-1 CARDINAL DIAMOND): For EACH SEED at (r, c) with color C: PAINT the 4 CARDINAL NEIGHBORS — (r-1, c), (r+1, c), (r, c-1), (r, c+1) — with COLOR C, clipping at grid edges. The seed cell stays. The result is a 5-cell plus-shape (or smaller if at border) in color C per seed. Net: each seed becomes a + diamond of its color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
