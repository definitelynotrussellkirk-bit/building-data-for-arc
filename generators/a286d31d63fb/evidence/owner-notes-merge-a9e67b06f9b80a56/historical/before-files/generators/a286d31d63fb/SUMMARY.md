# a286d31d63fb

0-bg grid (h~10-13, w~12-15) containing two kinds of CONNECTED COMPONENTS, each in a DISTINCT non-zero color: (a) 1-2 FLAT components — polyominoes where every row in the bbox has the SAME cell count (3-cell vertical line, 2x2 square, 2x3 solid); (b) 2 NON-FLAT components — polyominoes with VARYING per-row cell counts (T-shapes, L-shapes, S/Z-tetrominoes). Components are 1-cell padded. Rule: for EACH CONNECTED COMPONENT, normalize its cells and compute its PER-ROW CELL COUNT PROFILE. If all rows have the SAME cell count (FLAT), RECOLOR every cell to COLOR 8 (cyan). If the row profile VARIES (NON-FLAT), leave the component's color unchanged. Net: flat blobs become cyan; non-flat blobs keep their color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
