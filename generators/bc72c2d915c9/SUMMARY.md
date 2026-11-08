# bc72c2d915c9

0-bg grid with N (3-5) connected blobs in distinct non-zero colors. Each blob has a strictly distinct size from all others (so the size-rank is unambiguous). Blobs are placed with ≥1-cell buffer so they don't 4-touch. Rule: sort all 4-connected non-bg components by (size ASC, then top-row ASC, then left-col ASC). Recolor the i-th component to palette[i] where palette = [2, 3, 4, 6, 7, 8, 9]. Output: same shapes, new colors based on size-rank.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
