# b31e765ef780

0-bg grid (h~11-14, w~13-16) containing two kinds of CONNECTED COMPONENTS, each in a DISTINCT non-zero color: (a) 1-2 HOLED OBJECTS — frame-shaped polyominoes with an ENCLOSED 0-CELL HOLE inside (3x3 donut, 3x4 rect outline); (b) 2 SOLID DISTRACTOR objects — small polyominoes without enclosed holes. Objects are non-touching with 1-cell padding. Rule: for EACH connected component, check if it has an ENCLOSED 0-CELL inside its bbox (a bg cell that cannot reach the grid border via 4-conn through other 0 cells without crossing this component). If YES (holed), RECOLOR every cell of that component to COLOR 8 (cyan). If NO (solid), leave it unchanged. Net: holed blobs become cyan; solid blobs keep their color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
