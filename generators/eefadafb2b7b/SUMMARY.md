# eefadafb2b7b

Two exact red 2×2 blocks appear in canonical-scale grids with scattered cyan cells. The output is `[[8]]` iff one **8-connected** cyan component touches the one-cell ring around both red blocks; otherwise it is `[[0]]`.

Version 3.0.0 uses a four-profile cyclic curriculum. Every consecutive four default examples contains: a diagonal-only bridge that refutes 4-connectivity, a disconnected bounding-box decoy, a true bridge smaller than an unrelated cyan component, and two separately touched rings with no bridge. Noise is added only when the selected semantic profile remains intact; negative labels are never created by deleting cells from an accidental bridge.

Kind: `per_puzzle`. Rule pin: `1d44fc0f4360`.
