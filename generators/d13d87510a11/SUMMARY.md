# d13d87510a11

0-bg grid with: (a) ONE color-1 (blue) SRC anchor cell; (b) ONE color-2 (red) DST anchor cell at a different position; (c) one TEMPLATE blob of 2-5 cells in color 3, placed adjacent to or around the src anchor. Rule: compute translation vector (dr, dc) = (dst.r - src.r, dst.c - src.c). Translate the 3-blob by (dr, dc). On a fresh 0-canvas, paint the translated blob in color 2. Anchors are removed in output. Blob's translated position fits in-bounds.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
