# 978ea94724d3

Any rectangular colored grid (H rows × W cols, W ≤ 15) with ≥2 distinct colors. Rule: output is hconcat(g, g) — duplicate the input horizontally to produce an H × 2W grid where the right half is the SAME as the left half. Equivalent to output[r][c] = input[r][c mod W].

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
