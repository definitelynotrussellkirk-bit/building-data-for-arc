# 8fb95be218da

Grid split into N panels (~5-6) by 1-wide full-height color-9 (maroon) separator COLUMNS. Panel 0 = SOURCE motif; panel 1 = TARGET motif; panels 2..N-1 = CANDIDATES. Each panel has 1-3 cells in some non-{0,9} color. Rule: split panels. Compute source cells (panel-relative positions where panel value != 0); same for target. For each candidate panel, compute its cells, union with source's cells, then check if the UNION (sorted, deduped) equals target's cells. The FIRST candidate matching that test is selected. Output: that candidate panel with all non-zero cells recolored to 8 (cyan). If no match → empty (zeros) grid of candidate size.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
