# feaa89c467a0

4 PANELS in fixed 5-wide column windows [0..4], [6..10], [12..16], [18..22] of a 23-col grid (5-7 rows). Each panel holds ONE asymmetric shape (3-9 cells, all 8 dihedral images distinct) jittered to a random position inside its window, in an arbitrary color (the rule is COLOR-BLIND — it works on the binary crop). Panels are assigned to 1-4 shape CLASSES (each class a distinct cell-count so classes are pairwise dihedrally-inequivalent); each panel applies one of 8 dihedral transforms to its class base. Rule: binary-crop each panel; emit a 4x4 matrix where cell (r,c) is 8 on the diagonal, 2 if shape c is a ROTATION of panel r, 6 if it is a REFLECTION (dihedral, non-rotation) of panel r, else 0.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
