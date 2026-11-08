# 0f0d405d5bb8

0-bg grid (h~8-10, w~9-11) with: (a) ROW 0 cells (0, 1) and (0, 2) hold 2 DISTINCT PALETTE COLORS (from {2, 3, 4, 6, 7, 8} — non-1, non-9); (b) a HOLLOW COLOR-1 (blue) RECTANGULAR FRAME at (1, 1)..(h-2, w-2); (c) a COLOR-9 (maroon) SEED cell at (h//2, w//2) (center of frame interior). Rule (ALTERNATING CARDINAL RAYS FROM SEED): READ palette = [g[0][1], g[0][2]]. From the seed at (sr, sc), WALK in all 4 CARDINAL DIRECTIONS (up, down, left, right) STEP-BY-STEP until hitting a 1-wall. At step k (1-indexed), if the cell is 0, PAINT it with palette[k % 2]. The seed and frame stay. Net: alternating-color rays fill the frame interior from seed.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
