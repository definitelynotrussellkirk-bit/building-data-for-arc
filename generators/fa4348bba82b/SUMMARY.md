# fa4348bba82b

Grid (size varies) with ONE color-9 (maroon) PIVOT cell and 1-8 other colored cells (colors 1-8) scattered around it. Rule: take the (first) color-9 cell as the PIVOT. For EACH non-0/non-9 colored cell, compute its offset from the pivot and stamp the cell (keeping its color) at all FOUR 90-degree ROTATIONS of that offset about the pivot — 0, 90, 180 and 270 degrees — dropping any copy that falls outside the grid. OUTPUT a fresh grid containing the 9 pivot plus the 4-fold rotational orbit of every colored cell. Net: the scattered cells are completed into a 4-fold-rotationally-symmetric pattern around the maroon pivot.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
