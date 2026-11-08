# e927138d8305

0-bg grid (h~9-12, w~10-14) with: (a) a SOLID RECTANGLE (random 2x2..3x4) in rect_color; (b) a CONNECTED NON-RECTANGULAR polyomino (random, 4-6 cells, does not fill its bbox) in shape_color, separated from the rect. Rule: locate the solid-rectangle component and the non-rectangular component, crop the shape to its bbox, recolor its cells with the rect's color, output that crop. Varied shape forms + rect colours make the recolored crop differ per sample.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
