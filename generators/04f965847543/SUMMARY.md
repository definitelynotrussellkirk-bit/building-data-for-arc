# 04f965847543

0-bg grid with N (2-5) pairs of same-color cells positioned on a DIAGONAL 2-step apart (one cell at (r, c) and another at (r±2, c±2), with the (r±1, c±1) midpoint being 0). Pairs use distinct colors and are separated (1-cell buffer) so the rule's diagonal-midpoint test doesn't accidentally fire on other cell triples. Rule: scan every cell. If g[r][c] == g[r+2][c+2] (non-zero) AND g[r+1][c+1] == 0, set g[r+1][c+1] = g[r][c]. Same for anti-diagonal: g[r][c] == g[r+2][c-2] non-zero AND g[r+1][c-1] == 0 → fill.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
