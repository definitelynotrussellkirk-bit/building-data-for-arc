# 4e95d52c71b0

0-bg grid (h = dr+8, w = dc+8 with dr, dc ∈ [3, 5]) with: (a) SOURCE GRAY MARKER at (sr, sc) with sr, sc ∈ [2, 3] painted COLOR 5; (b) COLORED MOTIF — 4 cells around the source at offsets (0, 1), (1, 0), (1, 1), (2, 1) painted in 2 distinct non-{0, 5} colors (alternating); (c) ISOLATED GRAY MARKER at (sr + dr, sc + dc) — a second color-5 cell NOT adjacent to the source motif. Rule (USE GRAY-MARKER VECTOR TO TRANSLATE MOTIF, CLEAR ISOLATED GRAY): identify the TWO GRAY (5) MARKERS. SOURCE GRAY = the one ORTHOGONALLY ADJACENT to colored motif cells. ISOLATED GRAY = the one not adjacent to any non-gray non-bg. Compute DELTA = isolated_pos - source_pos. For EACH non-gray motif cell at (r, c) with color C: PAINT (r + delta_r, c + delta_c) with C (copy translated). ERASE the ISOLATED GRAY (set to 0). Source gray + original motif stay. Net: the motif gets copied to a translated location and the isolated marker disappears.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
