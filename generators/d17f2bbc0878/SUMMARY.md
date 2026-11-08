# d17f2bbc0878

0-bg grid (h×w, ~14-20 by ~14-20) with TWO non-overlapping regions of distinct non-zero colors: a BIG region (color A, high density, larger bbox, more cells) and a SMALL minority region (color B, fewer cells). Regions placed in separate quadrants/halves of the grid with ≥1 empty row/col between them. Color B's cell count is STRICTLY less than color A's. Rule: scan colors 1-9. Find the non-zero color with the FEWEST cells (the minority). Compute its bbox. Crop the input to that bbox. Output: cropped subgrid, preserving both majority and minority cells inside the bbox.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
