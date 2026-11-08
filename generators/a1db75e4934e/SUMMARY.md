# a1db75e4934e

0-bg grid (h~8-11, w~9-12) with 3 BLOBS, each in a DISTINCT non-zero COLOR (drawn from 1..9 without replacement) and with STRICTLY DISTINCT SIZES (3 unique sizes from range 2..6). Blobs are 4-conn connected components grown via grow_blob with no touching. Rule: identify all NON-BG BLOBS. SORT them by AREA DESCENDING (largest first). STACK them VERTICALLY in a new output grid, LEFT-ALIGNED, with a 1-ROW GAP between consecutive blobs. The output's WIDTH is the MAX BBOX WIDTH of the largest blob; the HEIGHT is the SUM of blob heights + gaps. Net: 3 blobs become a vertical stack sorted largest-to-smallest, left-aligned with 1-row gaps.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
