# df5e596e5e96

A 5-row input contains `N=3..5` width-5 panels at columns `0,6,12,...`, with one blank separator column between panels. Each panel is a 4-connected, single-color support of 4–8 cells. Crop each panel to its nonzero bounding box and compare **binary support**: foreground color and within-panel translation are irrelevant.

The output is an `N×N` relation matrix. Diagonal entries are 8. Off diagonal: exact normalized support is 1; a non-identity rotation is 2; a reflection/other dihedral image is 3; unrelated support is 0. Exact matching has priority over rotation, and rotation has priority over the full dihedral orbit.

Version `3.0.0` pins canonical rule hash `dd7b7aac9913`. Its four-slot constructive curriculum always includes a same-cell-count unrelated pair and a reflection relation; half of slots use multiple foreground colors, so complete three-demo lessons refute both the cell-count and color-sensitive shortcuts that fit every canonical pair. Panel order is shuffled deterministically to avoid teaching four fixed relation matrices.

Kind: `per_puzzle`. Imported baseline version: `2.2.2`; reviewed version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
