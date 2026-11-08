# 8a761b80b11b

0-bg grid (h~5-7, w~8-11) with 3-5 HORIZONTAL same-color RUNS — each run is a contiguous segment of non-zero cells in a single row, length 2-5, all the same color. Runs are separated by ≥1 bg cell. Different runs use varied colors (may repeat). At least one run has length ≥3 (so reduction is observable). Rule: extract horizontal runs (contiguous same-color segments in each row). Produce a FRESH empty grid. For each run with start col c1 and end col c2, paint ONLY the two endpoint cells (run_line, c1) and (run_line, c2) with the run's color. Interior cells of length≥3 runs become 0. Length-1 runs paint just that cell; length-2 runs paint both. Net: every run → just its endpoints.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
