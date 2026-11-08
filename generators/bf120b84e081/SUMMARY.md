# bf120b84e081

0-bg grid (h~8-10, w~9-11) with 2-3 distinct non-bg colors. For EACH color, EXACTLY TWO isolated single cells (the MARKERS) are placed at random non-adjacent positions (8-connectivity isolation between any two cells, so each cell is its own 4-component). Rule: for each color that appears in exactly TWO cells, treat the two cells as endpoints. PAINT an ELBOW PATH between them — an L-shaped 2-segment path going through some corner point (typically the cell at (r1, c2) or (r2, c1)) — in that color. The two endpoint cells stay. Net: each colored pair gets connected by an L-shaped path of its own color.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
