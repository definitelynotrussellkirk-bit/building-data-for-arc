# 5d9c166a8c3b

0-bg grid (h~13-15, w~14-16) with 4 disconnected small 1×2 / 2×1 COMPONENTS in a single non-{0, 2} color: 2 components stacked vertically on the LEFT (sharing similar rows but different columns) and 2 components in matching columns ROWS placed below (sharing similar columns but different rows). The components' BOUNDING BOXES overlap in row span or column span across pairs. Rule: compute each component's bbox. CLUSTER components whose bboxes share at least one COMMON ROW or one COMMON COLUMN into a merged group. For each cluster, compute the MERGED BBOX (axis-aligned tight box covering all member components). PAINT every cell inside each merged bbox with color 2 (red). Net: groups of aligned components fuse into solid red rectangles spanning their combined extents.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
