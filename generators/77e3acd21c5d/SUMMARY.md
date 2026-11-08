# 77e3acd21c5d

A background-colored grid contains one solid monochrome rectangle and 2–5 separated two-color rectangles. The monochrome rectangle defines the output size and fill color. Select the widest two-color rectangle; its minority-color cells are markers. Transfer each marker to the output using its distance from the nearest source edges. Exact row or column ties mirror to both corresponding output edges, and out-of-bounds projections are discarded.

The generator covers four canonical shape/palette/object-count profiles and cycles corner, row-tie, column-tie, both-axis-tie, and clipping branches with varied colors and width-preserving global transforms.

Kind: `per_puzzle`. Current version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
