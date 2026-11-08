# dd47ca15f98a

0-bg grid (h~9-12, w~9-14) with: (a) color-1 (blue) MARKER at (0,0); (b) color-2 (red) MARKER at offset (dr, dc) from blue — defines the translation VECTOR; (c) a small MOTIF (3-5 cells) in some non-{0,1,2} color placed apart from markers, with room to fit several translated copies. Rule: find p1 = color-1 cell, p2 = color-2 cell; vector = (p2 - p1). Extract motif cells (non-{0,1,2}). Output: fresh empty grid. For k = 0, 1, 2, ... while all translated cells (shifted by k*vector) stay in bounds, stamp the motif (with original colors). Stop when out-of-bounds. Markers DISAPPEAR in output.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
