# 1aa3cbf99113

0-bg grid (h, w ~8-16) with N_small (1-4) SMALL objects of size ≤3 (singles, pairs, triples) and N_large (1-3) LARGE objects of size ≥4 (rectangles, L/cross/blob/Z shapes, hollow rings). All objects are 4-disconnected (1-cell buffer); input colors drawn from non-{0, 2, 8} palette so the rule's output colors are unambiguous. Rule: extract all 4-conn non-bg objects. For each object: if obj-size ≤ 3 → recolor every cell to color 2 (red); if obj-size ≥ 4 → recolor to color 8 (cyan). Net: a size-thresholded recolor with cutoff at 3.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
