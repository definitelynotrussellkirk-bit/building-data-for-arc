# fc75ac9edd87

Rows 0 and 1 encode a two-stage query. Count the color-1 cells in row 0 to select an exact symmetry class: 1=left/right only, 2=up/down only, 3=both axes, and 4=no reflection symmetry. Count the color-2 cells in row 1 to select area rank 1 or 2. Filter the body objects to the requested class, sort them by decreasing area (top-left breaks ties), crop the ranked object to its bounding box, and recolor its occupied cells cyan (8).

Kind: `per_puzzle`. Imported version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
