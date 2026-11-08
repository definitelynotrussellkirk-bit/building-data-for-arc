# 9242a166dc9e

0-bg grid (h, w~7-10) with 2-4 DIAGONAL ENDPOINT PAIRS — each pair: TWO SAME-COLOR cells at diagonal offset ±1 from a MIDPOINT (r, c), at (r-dr, c-dc) and (r+dr, c+dc) where (dr, dc) ∈ {(1, 1), (1, -1)}. Midpoint is initially 0. Pairs are DISTINCT colors from {1..9}, placed non-touching (3×3 neighborhood padding). Rule (FILL MIDPOINT OF EACH DIAGONAL ENDPOINT PAIR): For EACH PAIR of same-color cells at (r1, c1) and (r2, c2) with |r2-r1| == |c2-c1| == 2 and the midpoint cell (r1+r2)//2, (c1+c2)//2 == 0: PAINT the midpoint with the pair's color. Endpoints stay. Net: each diagonal endpoint pair becomes a filled 3-cell diagonal.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
