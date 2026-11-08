# b16f601b9eb8

Grid (h, w ~12-18) filled with background color 8 (cyan) and 2-3 SOLID RECTANGLES of distinct non-bg colors. Rectangles have distinct AREAS (so a sort is unambiguous). Rectangles are placed without overlap. Rule: bg = color at (0, 0). Find non-bg, non-zero color components. Compute each component's bbox dimensions (bh, bw) and area = bh*bw. Sort by area descending. The LARGEST = canvas (oh × ow). Output: oh × ow grid where each cell (r, c) takes the color of the SMALLEST rect whose dims still cover (r, c) (i.e., (r, c) is inside the smaller rect's dims). Rects stack at top-left from largest to smallest.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
