# 6b6e3acc8a0a

0-bg grid with: (a) exactly one color-1 cell (source anchor); (b) exactly one color-2 cell (destination anchor); (c) one or more shapes in colors other than {0, 1, 2} (e.g. one connected blob in some color, OR multiple separate cells). Rule: compute translation (dr, dc) = pos(2) - pos(1). On a FRESH 0-grid, for every non-{0,1,2} input cell at (r, c) with value v, paint (r + dr, c + dc) with v if in-bounds (else drop). The two anchor cells (1 and 2) do NOT appear in the output; only the translated non-anchor cells are kept.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
