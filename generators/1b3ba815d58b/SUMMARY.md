# 1b3ba815d58b

0-bg grid (h, w~14-20) with 2-3 HOLLOW color-5 (gray) RECTANGULAR FRAMES of distinct sizes — interior widths from {2, 3, 4} (so outer sizes from {4, 5, 6}). Frames are placed by some position bias (scattered / row-aligned / col-aligned / diagonal / corners) with ≥1-cell margin between them. Rule: for each color-5 FRAME, compute its INTERIOR WIDTH iw (the bbox interior dimension). FILL the frame's interior cells with COLOR = iw + 5 — so width 2 → color 7 (orange), width 3 → color 8 (cyan), width 4 → color 9 (maroon). The gray frame border stays 5. Net: each frame's empty interior gets a width-keyed solid fill.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
