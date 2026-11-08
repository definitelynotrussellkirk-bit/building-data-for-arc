# 7529e1be2ed6

0-bg grid (h~9-12, w~11-15) with: (a) one CENTRAL color-3 (green) cell at random interior position (r, c); (b) 2-3 NEIGHBOR cells adjacent to it in distinct colors {2, 4, 6} (above/right/below the center); (c) 2 DISTRACTOR singletons (color 7, 8) elsewhere with no neighbors. Rule: extract all 4-conn non-bg components. For each, find its neighbor components (any 4-adjacent non-bg cell of a different color). KEEP components whose set of neighbor colors has SIZE ≥ 2; output them on a blank canvas (same dims). Drop components with <2 distinct neighbor colors.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
