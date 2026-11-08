# 1a66b7820adb

0-bg grid (h~6-9, w~8-11) with 3 BLOBS in DISTINCT non-zero colors (from 1..9) at non-touching positions (grow_blob with no shared cells). Each blob has 2-4 cells; blob shapes may vary. Rule (SORT BLOBS + HORIZONTAL GALLERY PACK): identify each BLOB as a connected component. SORT blobs by some criterion (e.g., size descending, color, or position). CROP each to its BBOX. PACK the crops HORIZONTALLY in sorted order, possibly with 1-COL GAPS. Output WIDTH = sum of bbox widths + gaps; HEIGHT = MAX bbox height. Net: 3 blobs → horizontal gallery in sorted order.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
