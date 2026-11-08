# 483d78b1d04b

0-bg grid (h, w~10-18) with: (a) EXACTLY 4 COLOR-5 (gray) MARKERS at the CORNERS of a RECTANGLE (r1, c1), (r1, c2), (r2, c1), (r2, c2) with r2-r1 ≥ 4, c2-c1 ≥ 4 in one of 5 RECT_SIZE kinds (small/medium/large/wide/tall) and 3 POSITION BIASES (spread/center/edge); (b) EXACTLY 1 NON-5 NONZERO CELL at rectangle CENTER ((r1+r2)//2, (c1+c2)//2) in a DRAW_COLOR from {1..9}\{5}. Rule (PAINT INSET RECTANGLE OUTLINE WITH DRAW COLOR): identify the 4 GRAY MARKERS (rectangle corners) and the NON-5 DRAW COLOR. PAINT the INSET RECTANGLE OUTLINE — rows r1+1, r2-1 and cols c1+1, c2-1 — in the DRAW COLOR. The 4 gray markers stay. The center draw-color cell may be kept or absorbed. Net: 4 gray corners outline a rect; rule draws a hollow inset rect inside in the marker color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
