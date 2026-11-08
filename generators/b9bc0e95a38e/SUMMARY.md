# b9bc0e95a38e

0-bg grid (h, w ∈ 9-16, by difficulty) with: ONE COLOR-8 (CYAN) SEED PIXEL placed at a position per POSITION_BIAS ∈ {center (rng), top_left (3, 3), top_right (3, w-4), bottom_left (h-4, 3), bottom_right (h-4, w-4)} with ≥3-cell margin from all edges. Rule (FROM THE CYAN SEED, EMIT A CLIPPED GRAY (5) STAIR PATTERN: ONE ARM GOES UP-RIGHT IN STAIR STEPS, ONE ARM GOES DOWN-LEFT IN STAIR STEPS; THE STAIRS ALTERNATE ONE-CELL HORIZONTAL AND ONE-CELL VERTICAL MOVES, PAINTED IN COLOR 5; SEED CELL PRESERVED AS COLOR 8): FIND the COLOR-8 seed at (sr, sc). EMIT UP-RIGHT ARM: walk alternating up-1, right-1, up-1, right-1 ... until hitting the grid edge, painting each cell COLOR 5. EMIT DOWN-LEFT ARM: walk alternating down-1, left-1, ... until edge, painting color 5. Seed stays cyan. Net: cyan dot grows a 2-arm gray stair pattern.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
