# 2826c36048c1

0-bg grid (h, w~6-8) with 2-3 DIAGONAL COLOR-8 (cyan) PAIRS: each pair is two 8-cells at diagonal positions in a 2×2 block — either MAIN diagonal {(r, c), (r+1, c+1)} or ANTI diagonal {(r, c+1), (r+1, c)}. The ANTI-DIAGONAL corners (the other 2 cells of the 2×2 block) are BG-0 initially. Pairs are placed at non-touching positions (Chebyshev distance ≥3 between centers). Rule (FILL ANTI-DIAGONAL CORNERS OF EACH 8-DIAGONAL PAIR WITH COLOR 1): For EACH 2×2 BLOCK containing an 8-DIAGONAL PAIR (two 8s at diagonal positions and two bg-0 cells at anti-diagonal positions): PAINT the anti-diagonal corner cells (the BG-0 cells) with COLOR 1. The 8-cells stay. Net: each diagonal 8-pair completes its 2×2 with blue corners on the opposite diagonal.

Kind: `per_puzzle`. Imported version: `1.1.1`.
Approval is derived by the catalog from current code and retained evidence.
