# 59c41de367b5

0-bg grid (h, w = fh+2 × fw+2 with fh, fw ∈ [6, 8]) with: (a) ONE HOLLOW RECTANGULAR FRAME at (1, 1)..(fh, fw) painted in a chosen FRAME COLOR (non-{0, seed_color}); (b) ONE SEED CELL at interior position (sr, sc) inside the frame in a SEED COLOR distinct from the frame color and 0. Rule (CHECKERBOARD-LIKE PARITY-FILL FROM SEED USING SEED AND FRAME COLORS): for EACH 0-CELL INSIDE the frame's interior at (r, c): compute MANHATTAN DISTANCE d = |r - sr| + |c - sc| from the seed. PAINT (r, c) with SEED COLOR if d is EVEN, with FRAME COLOR if d is ODD (or alternate per puzzle convention). The frame border and seed stay. Net: the interior is filled with a checkerboard pattern of seed/frame colors centered on the seed.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
