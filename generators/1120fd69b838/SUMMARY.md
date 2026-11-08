# 1120fd69b838

0-bg grid with N (2..6) 4-connected OBJECTS, each in a distinct color, placed apart by >=1 bg cell. Shapes are drawn from a pool of PAIRWISE-DIHEDRALLY-DISTINCT families; some families repeat (each instance independently rotated/flipped) to create dihedral-equivalent pairs. Rule: extract objects, sort by top-left (row, col), binary-crop each (drop color). Output: an N x N MATRIX where cell (r, c) = 8 (cyan) if mask[r] is DIHEDRAL EQUIVALENT to mask[c] (some transform code 1..8 maps one to the other), else 0. Diagonal always 8. Both N and the equivalence block-structure vary (was fixed 3x3).

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
