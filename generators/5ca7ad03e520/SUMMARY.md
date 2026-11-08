# 5ca7ad03e520

Grid split into N panels (~5-6) by 1-wide full-height color-9 (maroon) separator COLUMNS. Each panel of width panel_w (~4-5). Panel 0 holds a SOURCE motif (1-3 cells in some non-{0,9} color); remaining panels are CANDIDATES (each with their own 1-3 cell motif). Rule: split by color-9 cols. Normalize source's cells (anchored at (0,0)). For each candidate panel, normalize its cells the same way. Compare normalized cell-sets to source's. Output: 1×(N-1) strip where cell c is 8 (cyan) if candidate panel c's normalized cells match source's exactly, else 0.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
