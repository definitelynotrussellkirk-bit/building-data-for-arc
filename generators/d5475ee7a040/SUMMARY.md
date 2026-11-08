# d5475ee7a040

Square 0-bg grid (n×n, n~6-9) with 3 single-cell MARKERS in distinct colors placed off the main diagonal at positions (0, 2), (1, n-2), (n-3, 1). Rule: for every cell (r, c) with input != 0, ALSO paint the TRANSPOSED position (c, r) with the same color (keeping the original cell as well). Cells already on the main diagonal don't move (since (r, r) == (r, r)). Net: every off-diagonal mark gets mirrored across the main diagonal, doubling the non-bg cell count.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
