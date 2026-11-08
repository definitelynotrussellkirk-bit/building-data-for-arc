# 508ae94c035c

0-bg grid (h, w ~8-12) with 1-3 HORIZONTAL line objects (single-row runs of length 2-w) AND 1-3 VERTICAL line objects (single-column runs of length 2-h). All in distinct non-bg colors. Lines isolated by ≥1 bg cell. Rule: extract objects. Split into horizontal (all cells share one row) and vertical (share one col). Sort each group by (size DESC, color ASC). Top output row = horizontal lines laid out left-to-right, each painted in its color, separated by 1 zero. Bottom row = vertical lines (laid horizontally as runs of their color), separated by 1 zero. Output: 2-row grid sized to max(top, bottom).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
