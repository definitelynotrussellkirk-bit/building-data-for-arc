# 10aa0e361a4e

0-bg grid (h~9-11, w~11-13) with 3-4 ISOLATED 4-conn motifs (3-5 cells each) in distinct non-zero colors. Motifs separated by ≥1 bg cell. Rule: extract objects. For each object, compute 'grown size' — grow each cell by a square 3×3 stamp (8-conn neighborhood) and count the union size. Pick the object with MAX grown size (ties: tiebreak by scan order). Grow that object's cells by the same square stamp. Output: a small grid sized to the grown bbox, painted color 8 (cyan) at every grown cell, 0 elsewhere.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
