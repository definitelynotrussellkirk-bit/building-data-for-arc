# ad92d10d919c

0-bg grid (h~6-16, w~7-18) with 1-8 X-SHAPED MOTIFS — each motif places 4 SAME-COLOR cells at the DIAGONAL NEIGHBORS (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1) of an interior CENTER cell (r, c), with the center cell staying 0. Each motif's color is DISTINCT from {1..9}. Motif 3×3 neighborhoods are separated. Rule (DIAGONAL CONSENSUS FILL): For EACH INTERIOR 0-CELL (r, c): check its 4 DIAGONAL NEIGHBORS — if ALL ARE THE SAME NON-ZERO COLOR v, FILL (r, c) with v. X-motif centers satisfy this and become v. Other 0-cells stay 0. Net: each X-motif's center fills with its motif color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
