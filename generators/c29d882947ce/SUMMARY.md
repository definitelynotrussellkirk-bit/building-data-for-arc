# c29d882947ce

0-bg grid with 3-6 ISOLATED 4-connected components in distinct colors. Rule: extract all 4-connected components and sort by top-left (r1, c1). Output is an N×N MATRIX: out[i][j] = 1 if i == j; = 2 if shape[i] is rotation-equivalent to shape[j] under a 90° rotation; else 0. Net: encodes the pairwise rotation-equivalence relation among the components.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
