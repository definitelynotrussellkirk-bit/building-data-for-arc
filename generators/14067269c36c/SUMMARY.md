# 14067269c36c

0-bg grid (h~9-12, w~10-13) with: (a) exactly TWO color-1 (blue) cells aligned horizontally or vertically — these define a SPAN (Bresenham line, but here a straight line); (b) several non-1 blobs of distinct colors. EXACTLY ONE blob has cells that intersect the span (the target); the rest are distractors. Rule: take the first non-1 object whose cells touch the span. Crop it to its bbox and recolor ALL its non-bg cells to 8 (cyan), 0 elsewhere. Output is a small grid of just the target object's silhouette in cyan.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
