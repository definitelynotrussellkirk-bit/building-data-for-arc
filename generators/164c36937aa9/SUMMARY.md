# 164c36937aa9

0-bg grid (h~9-11, w~10-12) with: (a) one PROTOTYPE component — a color-8 (cyan) ORIGIN cell + 2-4 color-1 (blue) BODY cells connected to the origin; (b) 2-3 single-cell ANCHORS in distinct colors from {2, 3, 4, 5, 6, 7, 9} placed isolated elsewhere (≥3 Manhattan distance from the prototype). Rule: find the prototype (component containing color-8). Build a binary STAMP from the prototype's bbox (non-bg cells = 1, else 0). For each ANCHOR (single non-{0, 1, 8} cell), translate the stamp so the origin lands on the anchor, paint the stamp's '1' cells with the ANCHOR's color. Overlapping stamp cells become color 9.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
