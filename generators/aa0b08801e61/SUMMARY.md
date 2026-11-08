# aa0b08801e61

0-bg grid (size varies) with 3-6 non-touching BLOBS of arbitrary colors, each a shape constructed to belong to one of four SYMMETRY CLASSES (double-symmetric / left-right only / up-down only / asymmetric), with >=2 classes present. Rule: for each blob, classify its bbox cell-mask — LR-sym & UD-sym -> COLOR 8 (cyan); LR-sym only -> 2 (red); UD-sym only -> 3 (green); neither -> 4 (yellow) — and repaint it on a fresh grid. Input colors are irrelevant (the rule keys on shape). The grid size, blob count, and each blob's shape (which sets its output color) + position all vary freely (was 4 fixed shapes at fixed positions).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
