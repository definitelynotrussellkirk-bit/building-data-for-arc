# fe4b917edd70

Row 0 holds K nonzero 'marker' cells (any colors, any columns) — the rule reads K = the count of nonzero cells in row 0. Below row 0 are 2-5 connected objects, each a random polyomino of a DISTINCT size in a distinct color. Rule: K = nonzero count in row 0; take everything below row 0, sort those objects by size DESC (tiebreak top-row then left-col), and OUTPUT the bbox crop of the K-th largest.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
