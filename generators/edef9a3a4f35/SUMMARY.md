# edef9a3a4f35

0-bg grid with K (3-7) singleton non-zero cells, each in some color (1-9). The cells are placed so most have an empty cell at (r+1, c+1) (where they'd move) but ≥1 cell sits at the right or bottom edge — its (r+1, c+1) would be out of bounds, so it stays. Rule: scan all non-zero cells. For each, if (r+1, c+1) is in bounds AND empty in the input, write the value to (r+1, c+1) on a fresh output canvas. Otherwise, write it to (r, c) on the output. Output is a fresh 0-bg grid with the moved/staying cells.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
