# c5309d8fa84c

0-bg grid (h~8-10, w~11-13) with EXACTLY 3 NON-TOUCHING CONNECTED BLOBS at hardcoded positions: (a) a 4-cell L-tetromino at (1, 1); (b) a 4-cell T-shape at (1, 5); (c) a 3-cell corner at (h-4, w-4). Each in a DISTINCT non-zero color from {2..9}. NOTE: shapes/positions hardcoded — diversity is intrinsic-low. Rule: identify each non-bg CONNECTED COMPONENT. SORT them by COLOR ASCENDING. For each blob, CROP to its bbox. CONCATENATE the cropped bboxes HORIZONTALLY from left to right with 1-COL GAPS between them. Output: max-height-among-blobs × sum-of-widths + gaps. Net: input has scattered colored blobs; output is them side-by-side sorted by color in a horizontal pack.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
