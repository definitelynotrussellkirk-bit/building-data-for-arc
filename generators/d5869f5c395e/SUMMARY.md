# d5869f5c395e

0-bg grid (h ∈ 9-12, w ∈ 10-14) with: (a) ONE LEGEND MARKER at FIXED position (0, 0) — value ∈ {4, 5, 6} (legend codes that map to a target color, e.g., 5→2, 6→3, 4→4); (b) THREE COLOR-PAIRS scattered — for EACH color ∈ {2, 3, 4}: place 2 cells of that color at axis-aligned endpoints (horizontal or vertical, ≥3 cells apart, both cells initially 0). All 3 pairs placed via _try_pair with non-overlap check. Rule (READ THE LEGEND AT (0, 0), MAP TO A TARGET COLOR, FIND THE PAIR OF THAT COLOR, DRAW A COLOR-8 SPAN BETWEEN THE TWO CELLS): READ the (0, 0) LEGEND. MAP legend → target color (per demos: 5→2, 6→3, 4→4, etc.). FIND the two cells of the TARGET color (axis-aligned). PAINT every cell on the line segment between them (inclusive of endpoints) with COLOR 8 (cyan). Other pairs stay as-is. The legend cell stays. Net: legend selects which color-pair to connect; that pair becomes a cyan line.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
