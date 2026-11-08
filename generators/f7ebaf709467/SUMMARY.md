# f7ebaf709467

0-bg grid (size varies, up to ~16x20). Several single-cell colored SEEDS in distinct non-{0,5} colors, plus color-5 WALLS placed as short segments and dots. Rule: from each seed, BFS through open 0-cells (blocked by walls and other colors); paint every reachable 0-cell at EVEN BFS distance with the seed's color. Seeds and walls stay; overlapping halos resolve in row-major seed order. Net: each seed emits an every-other-ring halo that wraps around the walls. (Was: 8-10x9-11, 1-2 seeds, <=3 dot walls.)

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
