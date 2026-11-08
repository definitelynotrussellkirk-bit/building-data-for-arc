# a290047cba7e

0-bg grid (h~7-9, w~9-11) with 3 CONNECTED MOTIFS at distinct non-touching positions: sizes {2, 4, 6} (strictly different, shuffled), each painted in a DISTINCT non-{0, 7} color from {1, 2, 3, 4, 5, 6, 8, 9}. Motifs are 4-conn random walks, placed with 1-cell padding. Rule (RECOLOR MEDIAN MOTIF TO 7): identify all CONNECTED COMPONENTS. SORT them by SIZE (ASCENDING). The MEDIAN motif (middle one, position 1 in the sorted list of 3) gets RECOLORED to COLOR 7 (orange). The smallest (size 2) and largest (size 6) keep their original colors. Net: 3-blob input → median-size blob becomes orange; small/large blobs unchanged.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
