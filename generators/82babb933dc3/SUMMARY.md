# 82babb933dc3

0-bg grid (h~9-13, w~10-15) with 2-5 DISCONNECTED CONNECTED COMPONENTS in distinct non-bg colors. One component has STRICTLY LARGEST cell-count (size 7-11 cells), and the others are strictly smaller blobs (sizes decreasing). Each component is painted UNIFORMLY in a single color so the largest component is unambiguous. Rule: identify the UNIQUE LARGEST component (by cell count). CROP it to its bounding box, preserving its color. Output: the small cropped subgrid showing just the largest blob's cells (in its original color, with 0 elsewhere inside the bbox). All smaller blobs are discarded. Net: input is a multi-blob scene; output is the bbox of the biggest blob alone.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
