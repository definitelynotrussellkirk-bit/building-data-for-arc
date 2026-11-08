# c14c7af8df05

0-bg grid (h~7-10, w~7-10) with 2-4 TWO-CELL DIAGONAL COLOR CHAINS: for each chain, pick a distinct color from {1..9}, choose diagonal direction (down-right or down-left), pick a starting cell (r, c) so that the chain plus its one-step continuation fit in bounds. PAINT both chain cells (r, c) and (r+1, c±1) with the chain color. The THIRD cell at (r+2, c±2) is reserved (invariant: in-bounds and bg-0). Chains use disjoint cells; no two chains share any cell or extension cell. Rule (EXTEND EACH DIAGONAL CHAIN ONE MORE STEP): for EACH color C with exactly TWO cells forming a one-step diagonal (offset (+1, +1) or (+1, -1)): COMPUTE the continuation cell by extending one more step in the same diagonal direction. PAINT that continuation cell with COLOR C. Original two chain cells stay unchanged. Net: each two-cell diagonal becomes a three-cell diagonal of the same color, extending downward in the natural direction.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
