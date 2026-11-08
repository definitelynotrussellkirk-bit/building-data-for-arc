# ec23789c7821

0-bg grid with several horizontal color-runs of length 3 (each in its own color), placed away from grid top/bottom edges. Rule: for each cell that's part of an INTERIOR length-3 horizontal same-color run (where r > 0 and r < h-1), replace it with a vertical length-3 same-color run centered on the middle column of the original run: paint (r-1, c+1), (r, c+1), (r+1, c+1). Non-3-run cells are preserved. Output: each H-3 run becomes a V-3 run; rotation is around the center column.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
