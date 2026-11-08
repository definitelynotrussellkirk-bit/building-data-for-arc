# 2776235f38d3

0-bg grid (size varies). ONE color-1 (blue) SHAPE and ONE color-2 (red) SHAPE (random polyominoes whose normalized forms differ), placed apart, plus a color-7 (orange) NOISE cell the rule ignores. Rule: normalize each shape to its own bbox top-left, take the XOR (symmetric difference) of the two cell sets, and output it bbox-cropped with the XOR cells painted COLOR 8 (cyan). The grid size, the two shapes (which set the XOR output), their positions and the noise cell all vary freely, so the output varies too (was 2 fixed shapes + grid padding).

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
