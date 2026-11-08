# 5c65c477ef5f

0-bg grid (h~10-13, w~12-15) with 3-5 SEPARATED CONNECTED OBJECTS at scattered positions, each in a distinct color from {2..5}: (a) ONE small 3-cell L-shape TARGET object (strictly asymmetric — no lr/ud symmetry); (b) 1-3 LARGER asymmetric distractor blobs (4-5 cells, also no lr/ud symmetry); (c) ONE smaller or larger SYMMETRIC distractor (2×2 square, plus-shape, etc.). Objects don't touch each other. Rule: for EVERY connected object, check if it has NO horizontal AND NO vertical symmetry (i.e., is fully asymmetric). Among all ASYMMETRIC objects, find the SMALLEST one (strict minimum by cell count). CROP it to its bbox and RECOLOR every cell to color 8 (cyan). Output is just that cropped, recolored small subgrid. Net: input has several mixed-symmetry objects; output is the tiniest asymmetric one, alone, painted cyan.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
