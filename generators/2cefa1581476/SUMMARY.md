# 2cefa1581476

0-bg grid with N (3-5) connected components in distinct non-zero colors at scattered positions. Each component is a small 4-conn blob (3-5 cells) with varied bbox shape. Components are spaced ≥1-cell apart. Rule: extract each component. Crop to bbox. Sort by height descending (then color asc for ties). Pack the cropped pieces horizontally with 1-col gap between, ALL bottom-aligned. Output height = max cropped height; output width = sum cropped widths + (N-1) gaps.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
