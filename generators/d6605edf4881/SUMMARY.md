# d6605edf4881

0-bg grid (h, w~9-12) with 2-4 NON-TOUCHING BLOBS, each in a DISTINCT color drawn from 1..9 (shuffled), each of size 3-6 cells (4-conn random growth). Blobs are BBOX-ISOLATED (no bbox overlap with each other) and at least one blob is ASYMMETRIC (differs from its diagonal transpose). For each blob, the bbox transpose-within-grid is validated to fit in bounds. Rule (TRANSPOSE-WITHIN-BBOX UNION): for EACH BLOB, COMPUTE its BBOX (r1, c1, r2, c2). For each cell (r, c) of the blob, its TRANSPOSED POSITION within the bbox is (r1 + (c - c1), c1 + (r - r1)) — i.e., swap row and column OFFSETS from bbox top-left. PAINT both the original blob cells AND their transposed positions with the blob's COLOR. UNION the original and transposed cells. Other 0-cells stay 0. Net: each blob gains its bbox-local diagonal-transpose copy in the same color.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
