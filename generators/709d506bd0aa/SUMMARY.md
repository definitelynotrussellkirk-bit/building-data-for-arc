# 709d506bd0aa

0-bg grid (h~5-13, w~8-17) where each of `target` ACTIVE ROWS (2-9, drawn from h rows without repetition) holds 1-4 SCATTERED NON-0 CELLS at DISTINCT column positions in cols 1..w-1 (col 0 stays bg-0, ensuring leading zero before any non-zero, so packing has visible effect). Cell colors are drawn uniformly from {1..9}, with replacement (so a row may have duplicate colors but at distinct positions). Non-active rows stay all-0. At least one active row has leading or internal zeros (the col-0 bg constraint and sparse placement guarantee this). Rule (PER-ROW LEFT-PACK NON-ZERO VALUES, RIGHT-PAD WITH ZEROS): for EACH ROW r independently: collect every non-zero value in left-to-right order, preserving their RELATIVE ORDER. REPLACE the row with a left-packed sequence: place the collected values in cols 0, 1, 2, ... and fill the remaining right-side cells with 0. Empty rows stay all-0. Row dimensions are preserved. Net: each row is compacted to its left edge — sorted-by-position (not sorted-by-value), with the right side padded by bg-0.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
