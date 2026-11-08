# ca5dcbac0e83

0-bg grid (h~8-10, w~9-11) with 3-4 distinct non-zero COLORS, each appearing in exactly 2 isolated cells (8-conn non-adjacent). Rule: for each color with exactly 2 cells, compute a STAIRCASE PATH between them (monotone diagonal/L-step path). Collect all path cells across all color pairs. For each output cell (r, c), encode the count of how many path cells map to (r, c) via s17b-encode-count — a per-cell count map painted with specific colors per count level.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
