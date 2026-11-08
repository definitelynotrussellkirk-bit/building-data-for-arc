# ed658816cdb6

0-bg grid (h~9-13, w~10-14) with: (a) ONE COLOR-9 (maroon) ANCHOR cell at a random interior position; (b) 2-4 BLOBS in DISTINCT colors (sampled from [1..8]) of size 2-5 cells each. Each blob is at a STRICTLY DISTINCT Manhattan distance from the anchor (the min cell-to-anchor distance differs for every blob; no ties, so 'nearest' is unambiguous). Rule: identify the COLOR-9 ANCHOR and the non-9 BLOBS (color-keyed 4-connected components). For each blob, COMPUTE its MIN Manhattan distance to the anchor cell. KEEP only the BLOB with the SMALLEST distance, repainted in its original color on a BLANK grid; the anchor and all other blobs are ERASED to BG (0). Net: output is ONLY the nearest blob to where the 9-anchor was (no 9 in the output).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
