# abf3863c9aa5

0-bg grid (h~7-10, w~10-12) with 4 BLOBS each a 2-4 cell 4-connected blob grown via grow_blob, painted in a DISTINCT non-0 color drawn from a shuffled palette {1..9}. Each blob's BBOX WIDTH is STRICTLY DISTINCT from the other 3 (seen_widths set ensures no two blobs share width). Blobs are placed at non-touching non-overlapping positions via used-cell tracking. Rule (SORT BLOBS BY BBOX WIDTH ASCENDING, GALLERY-PACK HORIZONTALLY): extract every 4-CONNECTED non-bg COMPONENT. CROP each to its tight bbox. SORT crops by BBOX WIDTH ASCENDING (since widths are strictly distinct, sort is unambiguous). PACK the cropped blobs LEFT-TO-RIGHT in sorted order with a 1-column bg gap between consecutive crops, into a horizontal output grid. OUTPUT HEIGHT = max bbox_h across blobs; shorter crops are bottom-aligned (or top-aligned per demos). Net: 4 scattered blobs collapse into a horizontal gallery ordered by increasing width.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
