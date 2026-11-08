# 370e7fced412

Small grid (h, w~3-6) with n_colors (3-4) DISTINCT NONZERO COLORS at random positions, each with a DISTINCT COUNT determined by a distribution (uniform_gap/increasing/decreasing/polarized/powers). All counts are < total cells; max count ≤ grid_h (so bars fit). Palette kind: warm/cool/broad/primary. Rule (COLOR-COUNT BAR CHART): COUNT cells per COLOR (including 0). SORT colors by COUNT DESCENDING. EMIT OUTPUT GRID: each SORTED COLOR becomes a VERTICAL COLUMN in the output, with a BAR rising from the TOP (top cells = the color, lower cells = 0). The BAR HEIGHT = the color's count. Output dims: max(counts) × n_colors. Net: color-count histogram emitted as a top-to-bottom bar chart.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
