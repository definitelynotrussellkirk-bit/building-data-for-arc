# c7de5e8abc29

0-bg grid (h~6-10, w~9-14) with 2-3 PAIRS of SAME-COLOR CELLS, each pair on a DIAGONAL (|dr| == |dc| ≥ 2), direction drawn from {nw_se, ne_sw, mixed}. Each pair color is DISTINCT from a palette (warm/cool/broad/primary). Pairs don't share cells. Rule (CONNECT DIAGONAL SAME-COLOR PAIRS WITH DIAGONAL LINES): For EACH COLOR C with EXACTLY 2 cells (r1, c1) and (r2, c2) where |r2-r1| == |c2-c1| (diagonal): PAINT every cell along the DIAGONAL LINE between them in color C (Bresenham/step-1 diagonal). Endpoints stay. Net: each diagonal endpoint pair becomes a solid colored diagonal line.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
