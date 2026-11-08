# 564e67c1b7f4

0-bg grid (size varies). ONE color-2 SHAPE and ONE color-3 SHAPE, placed apart, defined over a shared k x k frame by a random per-cell membership: every cell belongs to shape-2, shape-3, both, or neither; both shapes span the full frame (so the rule's independent normalization keeps them aligned) and at least one cell belongs to BOTH. Plus a color-4 NOISE cell the rule ignores. Rule: normalize each shape to its bbox, INTERSECT the two cell sets, and output the intersection bbox-cropped in COLOR 8 (cyan). The grid size, the two shapes and their positions all vary freely (was 2 fixed shapes + grid padding).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
