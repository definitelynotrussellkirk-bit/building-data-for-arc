# 19496da22435

0-bg grid (h,w vary by difficulty). A color-7 (orange) hollow RECTANGULAR FRAME at a RANDOM position/size. ROW 0 holds BLUE (color 1) COLUMN markers; COL 0 holds RED (color 2) ROW markers. Some markers sit on columns/rows that are STRICTLY INSIDE the frame (a random subset of interior cols/rows) and some are DECOYS on cols/rows outside the frame. Rule (FILL ROW x COL INTERSECTIONS INSIDE THE FRAME): take the frame bbox; for each blue-marked col c and red-marked row r with the intersection (r,c) strictly inside the frame, paint (r,c) color 8 (cyan). Decoy intersections (one or both markers outside) stay empty. Grid size, frame placement, the interior marker lattice and the decoys all vary freely (was a fixed 10x12 grid with 6 hardcoded layouts).

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
