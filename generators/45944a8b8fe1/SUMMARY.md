# 45944a8b8fe1

FIXED 12×13 grid with: (a) LINE ROW at row ∈ {5, 6, 7}: a BROKEN HORIZONTAL RUN of LINE-COLOR painted at cols {2, 3, 8, 9} — two run segments (cols 2-3 and cols 8-9) with a GAP of 0s in cols 4-7 between them; (b) ANCHOR COLUMN: an anchor color is placed at TWO ROWS — UPPER ANCHOR at row ∈ {2, 3}, LOWER ANCHOR at row ∈ {8, 9}, both at ANCHOR_COL ∈ {10, 11}. Rule (COMPLETE BROKEN RUNS AND EXTEND COLORED COLUMNS UPWARD): (i) IDENTIFY the broken horizontal line: FILL the GAP (cols 4-7 of LINE_ROW) with the LINE-COLOR to complete the run; (ii) for the GAP COLUMNS just filled AND the ANCHOR COLUMN: EXTEND the line-color UPWARD from the line row toward each anchor (paint cells above the line row up to the anchor row in that column). Net: broken line completes and vertical bars project upward to anchor points.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
