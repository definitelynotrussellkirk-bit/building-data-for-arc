# 5f8201e3482c

0-bg grid (h×w, ~9-14 by ~12-17) with 2-5 connected motifs in distinct non-zero colors. Each motif is placed with ≥1-cell buffer. At least one motif has rows where its cells are non-contiguous (a gap between the leftmost and rightmost cell in some row). Rule: for each connected component, iterate over its rows. If a row has the component's color at multiple positions with at least one 0 between leftmost and rightmost, fill the entire span [leftmost..rightmost] with that component's color. Rows with no gap stay unchanged. Other components (no gaps) are preserved.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
