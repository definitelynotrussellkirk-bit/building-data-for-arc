# b1118feaedd5

0-bg grid (h, w~7-16) with: (a) 1-3 LARGE OBJECTS (size ≥ 3 cells) in some non-{0, 3} fg_color, shaped as rect / L / cross / random_blob / line_h / line_v; (b) 2-5 SMALL OBJECTS (size 1 or 2 cells) in the SAME fg_color — singletons or pairs (pair_h / pair_v / pair_diag). Large and small objects are 4-conn isolated with 1-cell padding. Rule: for EVERY 4-CONN OBJECT, compute its CELL COUNT. If size < 3 (singletons or pairs), RECOLOR every cell of that object to COLOR 3 (green). If size ≥ 3 (large), KEEP fg_color unchanged. Net: small objects turn green; large objects stay.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
