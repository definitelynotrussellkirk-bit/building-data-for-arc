# 5fa72382e059

Grid with: (a) a complete row OR complete column of color-8 cells (the 'guide line'); (b) one or more colored non-{0,8} cells on ONE side of the guide. Rule: detect the guide — if it's a full row at row gr, reflect non-guide non-bg cells across it by (r, c) → (2*gr - r, c). If it's a full column at col gc, reflect by (r, c) → (r, 2*gc - c). Output is a fresh 0-grid with only the reflected cells; the original cells and the 8-guide do NOT appear in the output. Reflected cells outside grid bounds are silently dropped.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
