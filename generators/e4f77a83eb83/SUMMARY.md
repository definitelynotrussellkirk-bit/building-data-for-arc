# e4f77a83eb83

0-bg grid (h~8-10, w~9-12) with 2-4 DIAGONAL PAIRS — each pair is two SAME-COLOR cells along the MAIN DIAGONAL (slope +1): pick length L ∈ {2..5}; pick start (r0, c0); endpoint at (r0+L, c0+L). PAINT only the two endpoints in the pair's color; cells (r0+k, c0+k) for k ∈ [1..L-1] are bg-0 (the diagonal span). Each pair uses a DISTINCT non-0 color drawn from {1..9}. Diagonal spans don't overlap (placement tracked in reserved set). Rule (FILL EACH MAIN-DIAGONAL SPAN BETWEEN SAME-COLOR ENDPOINTS WITH THAT COLOR): for EACH color C that appears at exactly TWO cells (r0, c0) and (r0+L, c0+L) on the SAME MAIN-DIAGONAL LINE (slope +1, equal row-step and col-step): PAINT every cell (r0+k, c0+k) for k in [1..L-1] with COLOR C. Endpoints stay. Anti-diagonal pairs and non-pair cells are unchanged. Net: each diagonal pair becomes a solid diagonal colored line.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
