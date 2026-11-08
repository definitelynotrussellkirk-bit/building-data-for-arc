# bdaef728db34

0-bg grid (h×w, ~6-9 by ~8-12) with 3-5 horizontal RUNS of non-zero cells. Each run: a contiguous horizontal segment of length 2-5 in a single non-zero color. Runs are placed in different rows or with ≥1 zero gap between same-row runs. Different runs use distinct colors (or repeat). Rule: for each cell, output the cell's color if it's the LEFTMOST of its same-color horizontal run (i.e., either col=0 or the cell to its left has a different color), else 0. Output: only the leftmost cell of each horizontal run survives.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
