# d3ca15d5889d

Canonical 3x3 grid where MOST cells share one non-{0,5} color (the MODE, 50-85% density) — call it keep. Remaining cells are 1-3 distractor colors (chosen from {1..9} ∖ {0, 5, keep}), optionally including bg(0). Rule: compute mode = most-frequent non-zero color in the input. For every cell (r, c): if cell value == mode, keep it; otherwise (including bg cells) → set to 5 (gray). Output: same shape as input, with the dominant color preserved and everything else recolored gray.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
