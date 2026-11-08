# 75ac106ed6a9

0-bg grid (h, w ~7-10) with 3-5 distinct non-bg colors, each occupying a DISTINCT cell count drawn from {2..7}, scattered uniformly. Total non-bg cells ≤ 30. Rule: collect (color, count) for each distinct non-bg color. Sort by DESCENDING count, ties broken by ASCENDING color value. Output is a 1×N row (N = total non-bg cell count) where each color appears CONSECUTIVELY repeated by its count, in sorted order. So a histogram-as-1D-bar-chart concatenated by frequency rank.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
