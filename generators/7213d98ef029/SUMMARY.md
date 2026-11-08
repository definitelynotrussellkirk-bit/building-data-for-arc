# 7213d98ef029 — marker equality matrix

The zero corner separates a nonzero column-header strip (top row) from a
nonzero row-header strip (left column). The interior is zero. After removing
both header axes, output cell `(r, c)` is the row-header color exactly when the
row and column headers are equal; otherwise it is zero.

The selected generator uses the four canonical output shapes, four observable
row/column set relationships, and five fixed nonzero palettes (four or five
colors). Every four consecutive default samples cover all four set
relationships and provide explicit evidence for off-diagonal equality,
inequality, row-only and column-only colors, and repeated shared colors.

Kind: `per_puzzle`. Selected version: `3.0.0`.
Canonical rule hash: `e5bbb5dc0c42`.
Final generator SHA-256: `46ef37fa96e213a9e51f1ae0e7891cdc9c4571cbc90f6a4dbe6bfe76970998d2`.
