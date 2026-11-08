# Solve work log

## Prior exposure

I had not seen this task's rule, generator, reference solution, private labels, or earlier solution explanation. Before solving I only saw the packet's general workflow documentation and the visible examples produced by `blind prepare`.

## Revision 1 — equality-table hypothesis

The nonzero values along the top row act as column labels, and the values down the first column act as row labels. Every demonstrated interior cell is filled with the shared color exactly when its row label equals its column label; all mismatches are zero. Header cells are unchanged. Zero labels therefore create no visible interior mark, which also explains the blank rows and columns in the examples.

Implemented `solve(grid)` by copying the input, then for each interior `(r, c)` writing `grid[r][0]` when `grid[r][0] == grid[0][c]`, else `0`. Added rectangular-input validation. No competing hypothesis remained after checking all three visible examples by inspection.
