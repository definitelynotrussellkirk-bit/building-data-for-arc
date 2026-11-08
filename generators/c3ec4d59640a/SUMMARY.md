# c3ec4d59640a

0-bg grid (h, w~6-17) with 3-10 SINGLETON MARKER cells in COLORS {2, 3, 4} at interior positions (1..h-2, 1..w-2) so their keyed shape stays in-bounds. Each marker's footprint (keyed shape + 1-cell guard) doesn't overlap other markers' footprints. Rule (EXPAND EACH MARKER TO ITS KEYED SHAPE ON FRESH CANVAS): EMIT a FRESH h×w OUTPUT GRID. For EACH SINGLETON MARKER at (r, c) with color: color 2 → STAMP HORIZONTAL BAR cells (r, c-1), (r, c), (r, c+1); color 3 → STAMP VERTICAL BAR (r-1, c), (r, c), (r+1, c); color 4 → STAMP PLUS-5 (centered + 4 cardinals). All stamped cells keep the marker's color. OOB cells are clipped. Net: each color-2/3/4 singleton becomes its keyed shape on a fresh canvas.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
