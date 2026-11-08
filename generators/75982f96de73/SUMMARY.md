# 75982f96de73

0-bg grid (h×w, h=4..6, w=4..6) with ROW 0 as a TOKEN SEQUENCE: 1-3 tokens at the leftmost columns, each in {1, 2, 3, 4} (1=rotate-cw, 2=flip-lr, 3=flip-ud, 4=transpose). Rest of row 0 is 0. Body (rows 1..h-1) contains exactly ONE connected SHAPE of 2-5 cells in some color != 0 and != {1, 2, 3, 4} tokens (typically 5, 6, 7, 8, 9), placed somewhere with at least one row of bg between it and row 0. Rule: read tokens. Crop body to non-zero bbox. Apply each token's transform in sequence. Output = final transformed shape (variable dimensions).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
