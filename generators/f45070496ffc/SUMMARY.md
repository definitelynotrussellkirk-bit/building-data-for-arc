# f45070496ffc

0-bg grid (h~8-13, w~7-11). Contains: (a) matching VERTICAL ENDPOINT PAIRS — two same-color cells at (r,c) and (r+2,c) with exactly one bg cell between; (b) DISTRACTORS the rule leaves alone — lone single cells (no vertical partner) and mismatched endpoint pairs (x 0 y, x!=y). All structures have a >=2-row vertical clearance so none interfere. Rule: for interior (r,c), if input[r][c]==0 AND input[r-1][c]!=0 AND input[r-1][c]==input[r+1][c] -> set output[r][c]=input[r-1][c]. Net: only the MATCHING 1-cell gaps fill; lone cells and mismatched pairs stay. (Canonical includes such distractors; prior version emitted matching pairs only.)

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
