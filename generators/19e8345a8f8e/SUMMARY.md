# 19e8345a8f8e

0-bg grid (h, w~9-11) with 3 SAME-SHAPE BLOBS each a 2×2 SOLID SQUARE in COLOR 1. The 3 blobs are placed at NON-TOUCHING positions (1-cell padding) so that their bbox-min-distance-to-grid-border values are all STRICTLY DISTINCT (Chebyshev distance from bbox to any of the 4 grid edges is the minimum of row-from-top, row-from-bottom, col-from-left, col-from-right). Rule (RECOLOR THE FARTHEST-FROM-BORDER BLOB TO COLOR 7): for EACH blob, compute its BBOX CENTER's DISTANCE to any GRID BORDER (Chebyshev). Find the blob with the STRICTLY MAXIMUM distance (the most interior blob). RECOLOR all cells of that blob from 1 to COLOR 7. Other blobs stay at 1. Net: the most interior blob turns orange; the border-adjacent blobs stay blue.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
