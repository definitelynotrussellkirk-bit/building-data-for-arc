# ab8640b4ed72

0-bg grid (h~7-10, w~8-12) with 2-4 SAME-COLOR ENDPOINT TRIPLES — each TRIPLE consists of two cells of a DISTINCT non-0 color separated by EXACTLY ONE ZERO CELL between them, either HORIZONTAL (r, c), (r, c+1)=0, (r, c+2) or VERTICAL (r, c), (r+1, c)=0, (r+2, c). Triples don't overlap or touch each other (via 8-conn clearance check). Colors are distinct across triples. Rule (BRIDGE THE MIDPOINT OF EACH DISTANCE-2 SAME-COLOR PAIR): For each pair of same-color cells at axis-aligned distance 2 (one 0 between them): find the MIDPOINT cell (the 0-cell between) and PAINT it with the pair's color. The endpoints stay. Net: each distance-2 axis-aligned same-color pair becomes a solid 3-cell line.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
