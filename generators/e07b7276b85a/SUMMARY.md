# e07b7276b85a

0-bg grid (h~8-10, w~7-10) with 2-4 ENDPOINT PAIRS in distinct non-bg colors. Each pair is AXIALLY ALIGNED (horizontal or vertical) with an EVEN SPAN between the two endpoints (span ∈ {2, 4, 6}, so there is a SINGLE integer MIDPOINT cell between them). Pairs don't overlap. The cells between the endpoints are 0. Rule: for each color appearing exactly TWICE at axially-aligned endpoints with an even span between them, COMPUTE the MIDPOINT cell (((r1+r2)/2, (c1+c2)/2)). PAINT that single midpoint cell with the pair's color. Endpoints stay; other cells in the span stay 0. Net: each endpoint pair gets its exact midpoint marked in the pair's color — no full bridge, just the center dot.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
